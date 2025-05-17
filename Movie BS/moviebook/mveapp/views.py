from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from collections import defaultdict
from .models import Registration, Movie, Location, Comment, Showtime, Seat, Snack, BookingDetail, SelectedSnack, Theatre, ContactMessage
from decimal import Decimal
import razorpay # type: ignore
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt


def index(request):
    return render(request, "index.html")

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            try:
                ContactMessage.objects.create(name=name, email=email, message=message)
                return JsonResponse({'status': 'success', 'message': 'Your message has been sent successfully!'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Error saving message: {str(e)}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Please fill in all the required fields.'})
    else:
        return render(request, 'contact.html')

def about(request):
    return render(request, "about.html")

def register(request): 
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        email = request.POST['email']
        phone = request.POST['phone']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        if pass1 == pass2:
            reg = Registration(username=username, fname=fname, email=email, phone=phone, pass1=pass1, pass2=pass2)
            reg.save()
            return redirect('login')
        else:
            messages.error(request, "Passwords do not match.")
    
    return render(request, "register.html")

def login(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        pwd = request.POST.get('password')

        try:
            reg = Registration.objects.get(username=name, pass1=pwd)
            request.session['user_id'] = reg.id
            request.session['username'] = reg.username  # Store username for later use
            messages.success(request, f"Welcome, {reg.username}!")
            return redirect('home')
        except Registration.DoesNotExist:
            messages.error(request, "Invalid username or password.")
    
    return render(request, "login.html")

def home(request):
    selected_location = request.GET.get('location', 'all')
    username = request.session.get('username', None)  # Get the stored username

    if selected_location == 'all':
        movies = Movie.objects.all()
    else:
        movies = Movie.objects.filter(location__name=selected_location)

    context = {
        'movies': movies,
        'selected_location': selected_location,
        'locations': Location.objects.all(),
        'username': username,  # Pass username to template
    }
    return render(request, 'home.html', context)


def moviedetail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    comments = Comment.objects.filter(movie=movie).order_by('-created_at')

    if request.method == "POST":
        user_id = request.session.get('user_id')
        if user_id:
            user = Registration.objects.get(id=user_id)
            content = request.POST.get('comment')
            if content:
                Comment.objects.create(movie=movie, user=user, content=content)
                messages.success(request, "Your comment has been posted.")
            else:
                messages.error(request, "Comment cannot be empty.")
        else:
            messages.error(request, "You need to log in to comment.")

        return redirect('moviedetail', movie_id=movie.id)

    return render(request, 'moviedetail.html', {'movie': movie, 'comments': comments})

def showtime_selection(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    showtimes = Showtime.objects.filter(movie=movie).order_by('date', 'time')
    grouped_showtimes = defaultdict(list)

    for showtime in showtimes:
        # Count total seats for the showtime
        total_seats = Seat.objects.filter(showtime=showtime).count()
        # Count booked seats for the showtime
        booked_seats = Seat.objects.filter(showtime=showtime, is_booked=True).count()
        # Add a flag to indicate if the showtime is fully booked
        showtime.is_fully_booked = (total_seats == booked_seats)
        grouped_showtimes[showtime.date].append(showtime)

    return render(request, 'showtime_selection.html', {
        'movie': movie,
        'grouped_showtimes': dict(grouped_showtimes)
    })

def seat_selection(request, showtime_id):
    showtime = get_object_or_404(Showtime, id=showtime_id)
    seats = Seat.objects.filter(showtime=showtime).order_by('row', 'number')
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "You must be logged in to book seats.")
        return redirect('login')

    if request.method == "POST":
        selected_seat_ids_str = request.POST.get("selected_seats", "")  # e.g., "1,2,3"
        selected_seat_ids = selected_seat_ids_str.split(",") if selected_seat_ids_str else []

        selected_seats = Seat.objects.filter(id__in=selected_seat_ids, showtime=showtime, is_booked=False)

        if selected_seats.count() == len(selected_seat_ids):
            # Store seat labels (for UI) and IDs (for booking) in session
            selected_seat_labels = [f"{seat.row}{seat.number}" for seat in selected_seats]
            request.session['selected_seats'] = selected_seat_labels
            request.session['selected_seat_ids'] = selected_seat_ids  # Save for later booking

            # Calculate and store seat total
            total_price = float(sum(seat.price for seat in selected_seats))
            request.session['seat_price'] = total_price
            request.session['showtime_id'] = showtime.id
            request.session['movie_id'] = showtime.movie.id
            request.session['theatre_id'] = showtime.theatre.id

            messages.success(request, "Seats selected successfully! Proceed to snacks.")
            return redirect('/select-snacks/')
        else:
            messages.error(request, "Some selected seats are no longer available. Please reselect.")
    else:
        messages.error(request, "Please select at least one seat.")

    context = {
        "showtime": showtime,
        "seats": seats,
        "seat_range": range(1, 11),
        "username": request.session.get('username'),
        "selected_seats": request.session.get('selected_seats', []),
    }
    return render(request, "seat_selection.html", context)


def select_snacks(request):
    snacks = Snack.objects.all()
    selected_seat_labels = request.session.get('selected_seats', [])
    total_seat_price = Decimal(request.session.get('seat_price', 0))

    if request.method == "POST":
        selected_snacks_data = {}
        snack_total = Decimal('0.00')

        for snack in snacks:
            qty_str = request.POST.get(f"snacks_{snack.id}", "0")
            if qty_str.isdigit():
                qty = int(qty_str)
                if qty > 0:
                    selected_snacks_data[str(snack.id)] = qty
                    snack_total += snack.price * qty

        # Store snack selections and price
        request.session['selected_snacks_data'] = selected_snacks_data
        request.session['snacks_total'] = float(snack_total)

        return redirect('payment_page')

    return render(request, 'snacks_selection.html', {
        'snacks': snacks,
        'selected_seats': selected_seat_labels,
        'seat_price': float(total_seat_price),
    })

def payment_page(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    # Session values
    selected_seat_labels = request.session.get("selected_seats", [])
    selected_snacks_data = request.session.get("selected_snacks_data", {})
    seat_price = Decimal(request.session.get("seat_price", 0))
    snacks_total = Decimal(request.session.get("snacks_total", 0))

    movie_id = request.session.get("movie_id")
    theatre_id = request.session.get("theatre_id")
    showtime_id = request.session.get("showtime_id")

    # Fetch related models
    user = get_object_or_404(Registration, id=user_id)
    movie = get_object_or_404(Movie, id=movie_id)
    theatre = get_object_or_404(Theatre, id=theatre_id)
    showtime = get_object_or_404(Showtime, id=showtime_id)

    # Process snack info with quantity and subtotal
    snacks_with_qty = []
    if selected_snacks_data:
        snack_ids = [int(snack_id) for snack_id in selected_snacks_data.keys()]
        selected_snacks = Snack.objects.filter(id__in=snack_ids)

        for snack in selected_snacks:
            qty = int(selected_snacks_data.get(str(snack.id), 0))
            if qty > 0:
                subtotal = snack.price * qty
                snacks_with_qty.append({
                    "snack": snack,
                    "quantity": qty,
                    "subtotal": subtotal
                })

    # Price calculations
    subtotal = seat_price + snacks_total
    gst_amount = subtotal * Decimal('0.18')
    final_amount = subtotal + gst_amount
    request.session["total_price"] = float(final_amount)

    # Razorpay order
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({
        "amount": int(final_amount * 100),  # Convert to paise
        "currency": "INR",
        "payment_capture": "1"
    })

    return render(request, "payment.html", {
        "user": user,
        "movie": movie,
        "theatre": theatre,
        "showtime": showtime,
        "selected_seats": selected_seat_labels,
        "snacks_with_qty": snacks_with_qty,
        "seat_price": float(seat_price),
        "snacks_total": float(snacks_total),
        "gst_amount": round(gst_amount, 2),
        "final_amount": round(final_amount, 2),
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    })


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        payment_id = request.POST.get("razorpay_payment_id")

        if payment_id:
            try:
                user_id = request.session.get("user_id")
                user = Registration.objects.get(id=user_id)

                showtime_id = request.session.get('showtime_id')  # Get showtime_id from session
                showtime = get_object_or_404(Showtime, id=showtime_id)

                # Step 1: Get selected seats, CORRECTLY FILTERED by showtime
                selected_seat_labels = request.session.get("selected_seats", [])
                seat_queries = [(seat[0], int(seat[1:])) for seat in selected_seat_labels]
                rows = [row for row, _ in seat_queries]
                numbers = [num for _, num in seat_queries]
                seats = Seat.objects.filter(row__in=rows, number__in=numbers, showtime=showtime)  #  Include showtime in the filter!

                # Ensure that the number of selected seats matches the number of seats fetched
                if seats.count() != len(selected_seat_labels):
                    return HttpResponse("Error: Incorrect number of seats fetched.  Possible data inconsistency.", status=500)
                
                for seat in seats:
                    seat.is_booked = True
                    seat.booked_by = user
                    seat.save()



                # Step 3: Create BookingDetail
                booking = BookingDetail.objects.create(
                    user=user,
                    movie=showtime.movie,
                    theater=showtime.theatre,
                    show_time=showtime,
                    payment_id=payment_id,
                    total_price=request.session.get("total_price", 0),
                    status="Booked",
                )
                booking.seats.set(seats)

                # Step 4: Save selected snacks
                selected_snacks_data = request.session.get("selected_snacks_data", {})
                for snack_id_str, quantity in selected_snacks_data.items():
                    snack = get_object_or_404(Snack, id=int(snack_id_str))
                    SelectedSnack.objects.create(
                        booking=booking,
                        snack=snack,
                        quantity=int(quantity)
                    )

                # Step 5: Clear session data
                request.session.pop("selected_seats", None)
                request.session.pop("selected_snacks_data", None)
                request.session.pop("total_price", None)

                messages.success(request, "Payment successful! Your ticket is booked.")
                return redirect("profile_view")

            except Exception as e:
                return HttpResponse(f"Error after payment: {str(e)}", status=500)

    messages.error(request, "Payment verification failed. Try again.")
    return redirect("payment_page")



def profile_view(request):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "You need to log in to view your profile.")
        return redirect('login')

    user = get_object_or_404(Registration, id=user_id)

    bookings = BookingDetail.objects.filter(user=user).select_related(
        'movie', 'theater', 'show_time'
    ).prefetch_related('seats', 'selected_snacks__snack').order_by('-booking_time')

    #  ⭐  CORRECTED SECTION: Filter seats by showtime  ⭐
    for booking in bookings:
        booking.booked_seats = booking.seats.filter(showtime=booking.show_time)

    return render(request, 'profile.html', {
        'user': user,
        'bookings': bookings
    })


def cancel_booking(request, booking_id):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')

    user = get_object_or_404(Registration, id=user_id)
    booking = get_object_or_404(BookingDetail, id=booking_id, user=user)

    # Mark the booking as cancelled
    booking.status = 'Cancelled'
    booking.save()

    # Unbook the seats and remove booked_by reference
    for seat in booking.seats.all():
        seat.is_booked = False
        seat.booked_by = None
        seat.save()

    messages.success(request, "Booking successfully cancelled.")
    return redirect('profile_view')

from django.db.models import Q  # ✅ Add this!

from django.utils import timezone

def transfer_ticket(request, booking_id):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')

        transfer_to = request.POST.get('transfer_to', '').strip()

        try:
            recipient = Registration.objects.get(Q(username=transfer_to) | Q(email=transfer_to)) #find Registration
        except Registration.DoesNotExist:
            messages.error(request, "The user you're trying to transfer the ticket to does not exist.")
            return redirect('profile_view')

        if recipient.id == user_id:
            messages.error(request, "You cannot transfer the ticket to yourself.")
            return redirect('profile_view')

        booking = get_object_or_404(BookingDetail, id=booking_id, user_id=user_id)

        if booking.status != 'Booked':
            messages.warning(request, "Only booked tickets can be transferred.")
            return redirect('profile_view')

        # Perform transfer
        booking.user = recipient
        booking.transferred_to = recipient #assign Registration
        booking.transfer_time = timezone.now()
        booking.status = 'Transferred'
        booking.save()

        for seat in booking.seats.all():
            seat.booked_by = recipient
            seat.save()

        messages.success(request, f"Ticket successfully transferred to {recipient.username}.")
    else:
        messages.error(request, "You are not authorized to transfer this booking.")

    return redirect('profile_view')




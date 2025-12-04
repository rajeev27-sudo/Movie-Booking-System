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
from django.urls import reverse
from django.utils.timezone import now
from datetime import timedelta


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

    user = Registration.objects.get(id=user_id)

    # 🔥 Auto-release expired seats before showing UI
    for seat in seats:
        seat.unlock_expired()

    if request.method == "POST":
        selected_seat_ids_str = request.POST.get("selected_seats", "")
        selected_seat_ids = selected_seat_ids_str.split(",") if selected_seat_ids_str else []

        selected_seats = []
        for seat_id in selected_seat_ids:
            seat = Seat.objects.get(id=seat_id, showtime=showtime)

            # ❌ If seat is locked by someone else → reject selection
            if seat.is_locked and seat.locked_by != user:
                messages.error(request, f"Seat {seat.row}{seat.number} is temporarily held by another user. Try again later.")
                return redirect(request.path)

            # ❌ Already booked → reject
            if seat.is_booked:
                messages.error(request, f"Seat {seat.row}{seat.number} is already booked.")
                return redirect(request.path)

            selected_seats.append(seat)

        # ✅ Lock seats for this user for 3 minutes
        for seat in selected_seats:
            seat.is_locked = True
            seat.locked_by = user
            seat.lock_expiry = now() + timedelta(minutes=3)
            seat.save()

        # Store in session
        selected_seat_labels = [f"{seat.row}{seat.number}" for seat in selected_seats]
        request.session['selected_seats_ids'] = selected_seat_ids
        request.session['selected_seat_labels'] = selected_seat_labels
        request.session['seat_price'] = float(sum(seat.price for seat in selected_seats))
        request.session['showtime_id'] = showtime.id
        request.session['movie_id'] = showtime.movie.id
        request.session['theatre_id'] = showtime.theatre.id

        messages.success(request, "Seats temporarily locked. Complete booking in the next 3 minutes.")
        return redirect('/select-snacks/')

    return render(request, "seat_selection.html", {
        "showtime": showtime,
        "seats": seats,
        "seat_range": range(1, 11),
        "username": request.session.get('username'),
        "selected_seats": request.session.get('selected_seats', []),
    })


def select_snacks(request):
    showtime_id = request.session.get("showtime_id") 
    snacks = Snack.objects.all()
    selected_seat_labels = request.session.get('selected_seat_labels', [])  # Fixed key
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
        'selected_seats': selected_seat_labels,  # Fixed key
        'seat_price': float(total_seat_price),
        "showtime_id": showtime_id, 
    })

def payment_page(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    # Session values
    selected_seat_labels = request.session.get("selected_seat_labels", [])  # Fixed key
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
                snacks_with_qty.append({
                    'snack': snack,
                    'quantity': qty,
                    'subtotal': snack.price * qty
                })

    # Calculate total price and GST
    total_price = seat_price + snacks_total
    gst_rate = Decimal('0.18')  # 18% GST
    gst_amount = total_price * gst_rate
    total_price_with_gst = total_price + gst_amount

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    razorpay_order = client.order.create({
        "amount": int(total_price_with_gst * 100),  # convert to paise
        "currency": "INR",
        "payment_capture": 1
    })

    razorpay_order_id = razorpay_order["id"]

    
    return render(request, "payment.html", {
        "selected_seats": selected_seat_labels,  # Fixed key
        "snacks_with_qty": snacks_with_qty,
        "seat_price": float(seat_price),
        "snacks_total": float(snacks_total),
        "total_price": float(total_price),
        "gst_amount": float(gst_amount),
        "total_price_with_gst": float(total_price_with_gst),
        "movie": movie,
        "theatre": theatre,
        "showtime": showtime,
        "razorpay_order_id": razorpay_order_id,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "final_amount": float(total_price_with_gst),
    })


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        payment_id = request.POST.get("razorpay_payment_id")

        if payment_id:
            try:
                user_id = request.session.get("user_id")
                if not user_id:
                    return HttpResponse("User not logged in.", status=403)
                user = Registration.objects.get(id=user_id)
                showtime_id = request.session.get('showtime_id')
                if not showtime_id:
                    return HttpResponse("Showtime missing from session.", status=400)
                showtime = get_object_or_404(Showtime, id=showtime_id)

                selected_seat_labels = request.session.get("selected_seat_labels", [])

                if not selected_seat_labels:
                    return HttpResponse("No seats found in session.", status=400)
                rows = []
                numbers = []

                for label in selected_seat_labels:
                    row = ''.join([c for c in label if c.isalpha()])
                    num = ''.join([c for c in label if c.isdigit()])

                    if not row or not num:
                        return HttpResponse(f"Invalid seat format: {label}", status=400)

                    rows.append(row)
                    numbers.append(int(num))
                seats = Seat.objects.filter(
                    showtime=showtime,
                    row__in=rows,
                    number__in=numbers
                )

                if seats.count() != len(selected_seat_labels):
                    return HttpResponse("Seat mismatch! Data inconsistency.", status=500)
                for seat in seats:
                    seat.is_booked = True         
                    seat.is_locked = False         
                    seat.locked_by = None         
                    seat.lock_expiry = None        
                    seat.booked_by = user         
                    seat.save()

                total_price = request.session.get("total_price", 0)

                booking = BookingDetail.objects.create(
                    user=user,
                    movie=showtime.movie,
                    theater=showtime.theatre,
                    show_time=showtime,
                    payment_id=payment_id,
                    total_price=total_price,
                    status="Booked",
                )

                booking.seats.set(seats)

                selected_snacks_data = request.session.get("selected_snacks_data", {})
                for snack_id_str, qty in selected_snacks_data.items():
                    snack = get_object_or_404(Snack, id=int(snack_id_str))
                    SelectedSnack.objects.create(
                        booking=booking,
                        snack=snack,
                        quantity=int(qty)
                    )
                # -----------------------------
                keys_to_clear = [
                    'selected_seat_labels',
                    'selected_seats',
                    'selected_seat_ids',
                    'selected_snacks_data',
                    'snacks_total',
                    'seat_price',
                    'showtime_id',
                    'movie_id',
                    'theatre_id',
                    'total_price',
                ]

                for key in keys_to_clear:
                    request.session.pop(key, None)

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

    
    booking.status = 'Cancelled'
    booking.save()

    
    for seat in booking.seats.all():
        seat.is_booked = False
        seat.booked_by = None
        seat.save()

    messages.success(request, "Booking successfully cancelled.")
    return redirect('profile_view')

from django.db.models import Q 

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
        booking.transferred_to = recipient 
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


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def release_lock(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return JsonResponse({"status": "no user"})

    # Get all seats locked by that user
    seats = Seat.objects.filter(locked_by_id=user_id, is_locked=True)

    for seat in seats:
        seat.is_locked = False
        seat.locked_by = None
        seat.locked_at = None
        seat.save()

    # Clear related session keys used during selection/payment so UI reflects release
    keys_to_clear = [
        'selected_seats_ids', 'selected_seat_ids', 'selected_seat_labels',
        'selected_seats', 'selected_seat_ids', 'selected_snacks_data',
        'snacks_total', 'seat_price', 'showtime_id', 'movie_id', 'theatre_id'
    ]
    for k in keys_to_clear:
        request.session.pop(k, None)

    return JsonResponse({"status": "released"})

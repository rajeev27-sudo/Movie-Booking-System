from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

# Registration Model
class Registration(models.Model):
    fname = models.CharField(max_length=100)
    email = models.EmailField()
    username = models.CharField(max_length=100)
    pass1 = models.CharField(max_length=100)
    pass2 = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.fname} ({self.username})"

# Login Model
class Login(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

# Location Model
class Location(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

#contactus
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

# Movie Model
class Movie(models.Model):
    GENRE_CHOICES = [
        ('Action', 'Action'),
        ('Comedy', 'Comedy'),
        ('Drama', 'Drama'),
        ('Horror', 'Horror'),
        ('Sci-Fi', 'Sci-Fi'),
        ('Romance', 'Romance'),
    ]

    LANGUAGE_CHOICES = [
        ('English', 'English'),
        ('Hindi', 'Hindi'),
        ('Malayalam', 'Malayalam'),
        ('Tamil', 'Tamil'),
        ('Telugu', 'Telugu'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    release_date = models.DateField()
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES)
    star_rating = models.FloatField(default=0.0)
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES)
    duration = models.DurationField()
    poster = models.ImageField(upload_to='movies/posters/', blank=True, null=True)
    location = models.ManyToManyField(Location)

    def __str__(self):
        return f"{self.title} ({self.language})"

class Cast(models.Model):
    movie = models.ForeignKey(Movie, related_name='cast', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='movies/cast/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.movie.title}"

class Comment(models.Model):
    movie = models.ForeignKey(Movie, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(Registration, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.movie.title}"

class Theatre(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theatre = models.ForeignKey(Theatre, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.movie.title} - {self.date} {self.time}"

class Seat(models.Model):
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE)
    row = models.CharField(max_length=1)  # A, B, C, D, E
    number = models.IntegerField()  # 1-15
    is_booked = models.BooleanField(default=False)
    booked_by = models.ForeignKey(Registration, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=100)  # Default price

    def book_seat(self, user):
        """Marks seat as booked by a user."""
        self.is_booked = True
        self.booked_by = user
        self.save()

    def __str__(self):
        return f"Seat {self.row}{self.number} - ₹{self.price} ({'Booked' if self.is_booked else 'Available'})"
    


class Snack(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='snacks/')

    def __str__(self):
        return self.name

class SelectedSnack(models.Model):
    booking = models.ForeignKey('BookingDetail', on_delete=models.CASCADE, related_name='selected_snacks')
    snack = models.ForeignKey(Snack, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        return self.quantity * self.snack.price

    def __str__(self):
        return f"{self.snack.name} x {self.quantity}"

class BookingDetail(models.Model):
    user = models.ForeignKey(Registration, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.SET_NULL, null=True)
    theater = models.ForeignKey(Theatre, on_delete=models.SET_NULL, null=True)
    show_time = models.ForeignKey(Showtime, on_delete=models.SET_NULL, null=True)
    seats = models.ManyToManyField(Seat)
    # snacks = models.ManyToManyField(Snack, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100)
    booking_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
    ('Booked', 'Booked'),
    ('Cancelled', 'Cancelled'),
    ('Transferred', 'Transferred')
], default='Booked')

    payment_id = models.CharField(max_length=255, blank=True, null=True)
    transferred_to = models.ForeignKey(Registration, on_delete=models.SET_NULL, null=True, blank=True, related_name='transferred_bookings')
    transfer_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
       return f"Booking by {self.user.username} - {self.movie.title if self.movie else 'No Movie'} - {self.status}"

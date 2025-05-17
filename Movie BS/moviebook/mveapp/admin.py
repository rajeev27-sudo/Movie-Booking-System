from django.contrib import admin
from .models import Registration, Login, Movie, Location, Cast, Comment, Theatre, Showtime, Seat, Snack, BookingDetail, SelectedSnack, ContactMessage

# Customize the Registration admin panel
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('username', 'fname', 'email', 'phone')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('username',)
    ordering = ('username',)
    readonly_fields = ('pass1', 'pass2')

# Customize the Login admin panel
@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    list_display = ('username', 'password')
    search_fields = ('username',)

# Customize the Movie admin panel
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'star_rating', 'get_locations')
    search_fields = ('title', 'genre')
    list_filter = ('genre',)
    ordering = ('title',)

    def get_locations(self, obj):
        return ", ".join([location.name for location in obj.location.all()])
    get_locations.short_description = 'Locations'

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Cast)
class CastAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'movie')
    search_fields = ('name', 'role', 'movie__title')
    list_filter = ('movie',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'created_at')
    search_fields = ('user__username', 'movie__title', 'content')
    list_filter = ('created_at', 'movie')

@admin.register(Theatre)
class TheatreAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    search_fields = ('name', 'location')

# Bulk Seat Generation Action
@admin.action(description="Generate Seats (Rows A-E, 10 seats per row)")
def generate_seats(modeladmin, request, queryset):
    rows = ['A', 'B', 'C', 'D', 'E']  # Define rows
    num_seats = 10  # 10 seats per row

    for showtime in queryset:
        seats = [
            Seat(row=row, number=number, showtime=showtime, is_booked=False)
            for row in rows
            for number in range(1, num_seats + 1)
        ]
        Seat.objects.bulk_create(seats)

    modeladmin.message_user(request, f"Seats added for {queryset.count()} showtimes.")

# Register Showtime with Bulk Seat Generation
@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ('movie', 'theatre', 'date', 'time')
    search_fields = ('movie__title', 'theatre__name')
    list_filter = ('date', 'theatre')
    actions = [generate_seats]  # Add bulk seat creation action

# Customizing Seat display
@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("showtime", "row", "number", "is_booked")
    list_filter = ("showtime", "is_booked")
    search_fields = ("showtime__movie__title", "row", "number")

admin.site.register(Snack)



@admin.register(SelectedSnack)
class SelectedSnackAdmin(admin.ModelAdmin):
    list_display = ('booking', 'snack', 'quantity')
class SelectedSnackInline(admin.TabularInline):
    model = SelectedSnack
    extra = 0
    readonly_fields = ['snack', 'quantity']


@admin.register(BookingDetail)
class BookingDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'theater', 'show_time', 'booking_time', 'total_price', 'status')
    list_filter = ('status', 'booking_time', 'movie', 'theater')
    search_fields = ('user__username', 'movie__title', 'theater__name', 'payment_id')
    ordering = ('-booking_time',)
    filter_horizontal = ('seats',)  # Makes many-to-many fields easier to manage
    inlines = [SelectedSnackInline]  # ✅ Add this line

admin.site.register(ContactMessage)
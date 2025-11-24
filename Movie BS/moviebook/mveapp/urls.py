from django.urls import path,include
from .import views
urlpatterns = [
   
    path('',views.index,name='index'),
    path('login',views.login,name='login'),
    path('register',views.register,name='register'),
    path('home',views.home,name='home'),
    path('about',views.about,name='about'),
    path('contact',views.contact,name='contact'),
    path('movie/<int:movie_id>/', views.moviedetail, name='moviedetail'),
    path('movie/<int:movie_id>/showtimes/', views.showtime_selection, name='showtime_selection'),
    path("movie/<int:showtime_id>/seats/", views.seat_selection, name="seat_selection"),
    path("select-snacks/", views.select_snacks, name="select_snacks"),
    path("payment/", views.payment_page, name="payment_page"),
 
    path('profile/', views.profile_view, name='profile'),

    path("payment-success/", views.payment_success, name="payment_success"),
    path('profile/', views.profile_view, name='profile_view'), 
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('transfer/<int:booking_id>/', views.transfer_ticket, name='transfer_ticket'),

    path("release-lock/", views.release_lock, name="release-lock"),


]


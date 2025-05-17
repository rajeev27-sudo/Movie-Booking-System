The Online Movie Ticket Booking System is a web-based application developed using Python (Django), HTML, CSS, and JavaScript. It is designed to streamline the process of movie ticket booking by allowing users to search for movies, select shows, choose seats, add snacks, and complete payments, all in a few clicks.
The system provides an intuitive interface for end users and offers administrative functionality for managing movies, shows, theaters, and booking records.

Key Features:
User Registration & Login: Custom authentication using session-based login. Users can register and securely log in to book tickets and manage their profile.

Movie Browsing: Displays current and upcoming movies with details like title, genre, rating, and posters. Location-based filtering of movies.

Seat Selection & Booking: Real-time seat selection from available seats. Prevents double-booking by marking seats as booked after confirmation.

Snack Selection: Option to choose multiple snacks with quantity before final checkout. Snacks are linked to the booking and displayed in the booking summary.

Payment Integration: Includes payment ID tracking (mock/real integration can be plugged in).

Booking History: Users can view their past and current bookings with movie, theater, seat, and snack details.

Ticket Transfer Functionality: Users can transfer tickets to other users by entering their username/email. Transferred tickets show the status as "Transferred" with the sender’s name.

Cancel Bookings: Allows users to cancel bookings before the show starts. Cancelled tickets update seat availability accordingly.

Technologies Used:
Backend: Python, Django

Frontend: HTML, CSS, Bootstrap (or custom CSS), JavaScript

Database: SQLite (or any RDBMS supported by Django)

Tools: Razorpay (or dummy payment), Django Admin, Git, VS Code


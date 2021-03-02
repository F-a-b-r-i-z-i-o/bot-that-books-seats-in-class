# bot-that-books-seats-in-class

The python version used is 3.9.2
The version of library telebot used is telebot 0.0.4

The bot was created by querying the website of the university of perugia, mathematics and computer science department.

BOT OPERATION:
A post request is made to the site, where some html tags are 'parsed', then the results found are printed.
After having printed the results, buttons open where it is possible to book a possible physical lesson,
or participate in a possible online lesson, and it is also possible to check the website dedicated to the teacher of the course found.

If you want to participate in the online lesson
click on the dedicated button and you will be sent back to the link of the lesson.

If you want to book a lesson on site
click here on the dedicated button and a seat is occupied.

The physical booking system
it is managed through a local db, where all you do is add or remove the booking made by a given student.

The 'anti-forgery' method
that we used comes into play through the booking.
When a student books a seat, their telegram id is printed, which will surely match that person.
In order not to create confusion, the teacher can ask students to change their telegram id with their matriculation or with their name and surname when acquiring a reservation.

To save classroom seat reservations a small sqlite3 db was created.

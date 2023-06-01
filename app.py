from flask import Flask, render_template, request, redirect, session
from datetime import datetime
import mysql.connector
import re
import bcrypt

app = Flask(__name__)

app.secret_key = "secret"

database = mysql.connector.connect(
    host="localhost", user="root", password="mysql-18", database="raildb"
)

cursor = database.cursor()


@app.route("/", methods=["POST", "GET"])
def main():
    if request.method == "GET":
        if "logged_in" in session:
            return render_template("newmain_user.html", name=session["name"])
        else:
            return render_template("newmain.html")

    else:
        print("HOW IT IS HERE")
        return render_template("search_results.html")


def hash_password(password):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password


def verify_password(password, hashed_password):
    # Verify the password against the hashed password
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    msg = ""

    if (
        request.method == "POST"
        and "name" in request.form
        and "surname" in request.form
        and "mail" in request.form
        and "phone_number" in request.form
        and "password" in request.form
        and "confirm_password" in request.form
    ):
        name = request.form["name"]
        surname = request.form["surname"]
        mail = request.form["mail"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        phone_number = request.form["phone_number"]

        cursor.execute("select * from Account where Email = %s", (mail,))
        account = cursor.fetchone()

        if account:
            msg = "Account already exits!"
            return render_template("signup.html", msg=msg)
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", mail):
            msg = "Invalid email address"
            return render_template("signup.html", msg=msg)
        elif not name or not password or not mail:
            msg = "Please fill the form"
            return render_template("signup.html", msg=msg)
        elif password != confirm_password:
            msg = "Passwords does not match"
            return render_template("signup.html", msg=msg)
        else:
            # register and persist credientials to db
            password_hash = hash_password(password)
            print(
                name,
                surname,
                mail,
                phone_number,
                password,
                confirm_password,
                password_hash,
            )
            cursor.execute(
                "insert into Account(Name, Last_Name, Email, Phone_Number, Password_Hash)"
                "values(%s,%s,%s,%s,%s)",
                (name, surname, mail, phone_number, password_hash),
            )
            database.commit()

            return redirect("/")

    return render_template("signup.html", msg=msg)


@app.route("/login", methods=["POST", "GET"])
def login():
    msg = ""

    if (
        request.method == "POST"
        and "mail" in request.form
        and "password" in request.form
    ):
        mail = request.form["mail"]
        password = request.form["password"]
        cursor.execute(
            "select * from Account where Email = %s",
            (mail,),
        )
        account = cursor.fetchone()

        if account and verify_password(password, account[5]):
            session["logged_in"] = True
            session["id"] = account[0]
            session["name"] = account[1]
            session["mail"] = account[3]

            return redirect("/")

        else:
            msg = "Wrong mail address or password!"
            print("Wrong mail address or password!")

    return render_template("login.html", msg=msg)


# logout icin bir app, session['logged_in] = false yapicak. Sonra maine yonlendir.
@app.route("/login/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("id", None)
    session.pop("mail", None)
    return redirect("/")


@app.route("/results", methods=["POST"])
def results():
    if "logged_in" in session:
        if request.method == "POST":
            from_point = request.form["from_point"]
            to_point = request.form["to_point"]
            date_str = request.form["date"]
            date_object = datetime.strptime(date_str, "%Y-%m-%d")
            # number_of_passenger = request.form["number_of_passenger"]

            cursor.execute(
                "select * from Trip where Departure_Location = %s and Destination_Location = %s and Departure_Date = %s",
                [from_point, to_point, date_object],
            )
            results = cursor.fetchall()

            return render_template(
                "search_results.html", data=results, name=session["name"]
            )
    else:
        msg = "Please Log In First"
        return render_template("login_with_warn.html", msg=msg)


@app.route("/reservations", methods=["POST", "GET"])
def reservations():
    if request.method == "POST":
        selected_trip_id = request.form["selected_trip"]
        # first check if the trip_id exist and correct
        # get the trip status, check
        # if ok, add trip to reservations
        # else , return err

        # cursor.execute("select * from Trip where Trip_ID = %s", ([selected_trip_id]))
        # selected_trip = cursor.fetchone()
        # print("trip information", id, "and train id equals to:", selected_trip[7])
        # train_id = selected_trip[7]

        cursor.execute(
            "select * from Trip_Status where Trip_ID = %s", ([selected_trip_id])
        )
        selected_trip = cursor.fetchone()

        print("this is trip_status information for train capacity", selected_trip)
        if selected_trip[2] < 1:  # if trip is full, gives warning
            msg = "this trip if full"
            return render_template("reservations.html", name=session["name"], mgs=msg)
        else:  # if trip is available, reserves a seat and updating trip information
            booked_seats = selected_trip[1] + 1
            available_seats = selected_trip[2] - 1
            print(booked_seats, available_seats, selected_trip_id)
            cursor.execute(
                "update Trip_Status set Total_Booked_Seats = %s, Total_Available_Seats = %s where Trip_ID = %s",
                [booked_seats, available_seats, selected_trip_id],
            )
            database.commit()

        cursor.execute(
            "insert into Reservation(Account_ID, Trip_ID)" "values(%s,%s)",
            [session["id"], selected_trip_id],
        )
        database.commit()

        return render_template("reservations.html", name=session["name"])

    elif request.method == "GET":
        cursor.execute(
            "select * from Reservation where Account_ID = %s", ([session["id"]])
        )
        res = cursor.fetchall()

        # collect trip information
        trips = []
        for trip in res:
            cursor.execute("select * from Trip where Trip_ID = %s", ([trip[2]]))
            current_trip = cursor.fetchone()

            temp_list = []
            temp_list.append(trip[0])
            for j in range(8):
                temp_list.append(current_trip[j])
            trips.append(temp_list)

        return render_template("reservations.html", name=session["name"], data=trips)


@app.route("/delete", methods=["POST"])
def delete():
    if request.method == "POST":
        # check if the deletion of the requested PNR number is valid and exists in reservations
        cancel_trip_pnr_string = request.form["delete"]
        pnr_cancel_request = int(cancel_trip_pnr_string)

        cursor.execute(
            "select * from Reservation where PNR = %s",
            [pnr_cancel_request],
        )
        trip_id = cursor.fetchone()[2]

        cursor.execute(
            "delete from Reservation where PNR = %s",
            [pnr_cancel_request],
        )
        database.commit()

        # update the trip_status info
        cursor.execute(
            "select * from Trip_Status where Trip_ID = %s",
            [trip_id],
        )
        previous_trip_status = cursor.fetchone()

        total_booked_seats = previous_trip_status[1] - 1
        total_available_seats = previous_trip_status[2] + 1
        cursor.execute(
            "update Trip_Status set Total_Booked_Seats = %s, Total_Available_Seats = %s where trip_id = %s",
            [total_booked_seats, total_available_seats, trip_id],
        )
        database.commit()

        return redirect("/reservations")


if __name__ == "__main__":
    app.run()

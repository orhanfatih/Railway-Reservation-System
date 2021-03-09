from flask import Flask, render_template, request, redirect, session
import mysql.connector
import re

app = Flask(__name__)

app.secret_key = 'secret'

database = mysql.connector.connect(host="localhost",
                                   user="root",
                                   password="Amd-13",
                                   database="test")

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


@app.route("/signup", methods=["POST", "GET"])
def signup():
    msg = ""

    if request.method == "POST" and "name" in request.form and "surname" in request.form and "mail" in request.form \
            and "phone_number" in request.form and "password" in request.form and "confirm_password" in request.form:
        name = request.form["name"]
        surname = request.form["surname"]
        mail = request.form["mail"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        phone_number = request.form["phone_number"]

        cursor.execute("select * from Accounts where mail = %s", (mail,))
        account = cursor.fetchone()

        if account:
            print("1")
            msg = "Account already exits!"
            return render_template("signup.html", msg=msg)
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', mail):
            print("2")
            msg = "Invalid email address"
            return render_template("signup.html", msg=msg)
        elif not name or not password or not mail:
            print("3")
            msg = "Please fill the form"
            return render_template("signup.html", msg=msg)
        elif password != confirm_password:
            print("4")
            msg = "Passwords are not match"
            return render_template("signup.html", msg=msg)
        else:
            print("Bilgiler dogru ve buraya kadar geldi")
            print(name, surname, mail, phone_number, password, confirm_password)
            cursor.execute("insert into Accounts(name, surname, mail, phone_number, user_password)"
                           "values(%s,%s,%s,%s,%s)", (name, surname, mail, phone_number, password))

            database.commit()

            return redirect("/")

    # elif request.method == "POST":
    #     msg = "Please fill the form"
    print("5")
    return render_template("signup.html", msg=msg)


@app.route("/login", methods=["POST", "GET"])
def login():
    msg = ""

    if request.method == "POST" and "mail" in request.form and "password" in request.form:
        mail = request.form["mail"]
        password = request.form["password"]

        cursor.execute("select * from Accounts where mail = %s and user_password = %s", (mail, password,))
        account = cursor.fetchone()

        if account:
            session["logged_in"] = True
            session["id"] = account[0]
            session["name"] = account[1]
            session["mail"] = account[3]

            return redirect("/")

        else:
            msg = "Wrong mail address or password!"
            print("Wrong mail address or password!")

    return render_template("login.html", msg=msg)


## logout icin bir app, session['logged_in] = false yapicak. Sonra maine yonlendir.
@app.route('/login/logout')
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
            date = request.form["date"]
            num_pass = request.form["num_pass"]

            cursor.execute("select * from Trip where from_trip = %s and to_trip = %s and departure_date = %s",
                           [from_point, to_point, date])
            results = cursor.fetchall()

            return render_template("search_results.html", data=results, name=session["name"])
    else:
        msg = "Please Log In First"
        return render_template("login_with_warn.html", msg=msg)


@app.route("/reservations", methods=["POST", "GET"])
def reservations():
    if request.method == "POST":

        selected_trip = request.form["selected_trip"]

        ## ---sonra trip e gidip trenin id al--------, trenin id ile trip statusten dus
        cursor.execute("select * from Trip where trip_id = %s", ([selected_trip]))
        id = cursor.fetchone()
        print("trip information", id, "and train id equalts to:", id[7])
        train_id = id[7]

        # Getting Status Information of Train in Trip
        cursor.execute("select * from Trip_Status where train_id = %s", ([train_id]))
        train = cursor.fetchone()
        print("this is trip status information for train capacity")
        if train[1] < 1:  # if trip is full, gives warning
            msg = "this trip if full"
            return render_template("reservations.html", name=session["name"], mgs=msg)
        else:  # if trip is available than reserves a seat and updating trip information
            booked_seats = train[0] + 1
            available_seats = train[1] - 1
            cursor.execute(
                "update Trip_Status set number_of_booked_seats = %s, available_seats = %s where train_id = %s",
                [booked_seats, available_seats, train_id])
            database.commit()

        cursor.execute("insert into Reservation(selected_trip, mail)"
                       "values(%s,%s)", [selected_trip, session["mail"]])
        database.commit()

        return render_template("reservations.html", name=session["name"])
        # return render_template("reservations.html", data=reservation, name=session["name"])

    elif request.method == "GET":
        cursor.execute("select * from Reservation where mail = %s", ([session["mail"]]))
        res = cursor.fetchall()  ### triplerin idler alindi

        ## Getted Trips
        trips = []
        for trip in res:  ## herbir trip icin reservasyondan trip_id al sonra gidip tripin infosunu listeye ekle

            cursor.execute("select * from Trip where trip_ID = %s", ([trip[1]]))
            get_trip = cursor.fetchone()

            ## pnr, trip id and mail data added to the list
            temp_list = []
            for k in range(3):
                temp_list.append(trip[k])
            for j in range(6):
                temp_list.append(get_trip[j + 1])
            trips.append(temp_list)

        return render_template("reservations.html", name=session["name"], data=trips)


@app.route("/delete", methods=["POST"])
def delete():
    if request.method == "POST":
        deleting_trip = request.form["delete"]
        deleting = int(deleting_trip)
        cursor.execute("delete from Reservation where pnr = %s", [deleting])
        database.commit()

        return redirect("/reservations")


if __name__ == '__main__':
    app.run()

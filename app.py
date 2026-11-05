
import os
from datetime import date, datetime
from decimal import Decimal
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash


# --------------------------------------------------
# FLASK APPLICATION CONFIGURATION
# --------------------------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-secret-before-deployment"
)

# PostgreSQL database for Render, SQLite for local development
database_url = os.environ.get("DATABASE_URL", "sqlite:///hospital.db")

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --------------------------------------------------
# DATABASE MODELS
# --------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(250))

    appointments = db.relationship(
        "Appointment",
        backref="patient",
        cascade="all, delete-orphan"
    )


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    appointments = db.relationship(
        "Appointment",
        backref="doctor"
    )


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patient.id"),
        nullable=False
    )
    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctor.id"),
        nullable=False
    )
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(10), nullable=False)
    status = db.Column(
        db.String(30),
        default="Scheduled",
        nullable=False
    )

    prescription = db.relationship(
        "Prescription",
        backref="appointment",
        uselist=False,
        cascade="all, delete-orphan"
    )

    bill = db.relationship(
        "Bill",
        backref="appointment",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointment.id"),
        unique=True,
        nullable=False
    )
    diagnosis = db.Column(db.Text, nullable=False)
    medicines = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointment.id"),
        unique=True,
        nullable=False
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(
        db.String(20),
        default="Unpaid",
        nullable=False
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# --------------------------------------------------
# LOGIN REQUIRED DECORATOR
# --------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):

            session["user_id"] = user.id
            session["username"] = user.username

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
@login_required
def dashboard():

    stats = {
        "patients": Patient.query.count(),
        "doctors": Doctor.query.count(),
        "appointments": Appointment.query.count(),

        "revenue": db.session.query(
            func.coalesce(func.sum(Bill.amount), 0)
        ).filter_by(payment_status="Paid").scalar()
    }

    recent = Appointment.query.order_by(
        Appointment.appointment_date.desc(),
        Appointment.id.desc()
    ).limit(6).all()

    return render_template(
        "dashboard.html",
        stats=stats,
        recent=recent
    )


# --------------------------------------------------
# PATIENT MANAGEMENT
# --------------------------------------------------

@app.route("/patients", methods=["GET", "POST"])
@login_required
def patients():

    if request.method == "POST":

        p = Patient(
            name=request.form["name"].strip(),
            age=int(request.form["age"]),
            gender=request.form["gender"],
            phone=request.form["phone"].strip(),
            address=request.form.get("address", "").strip()
        )

        db.session.add(p)
        db.session.commit()

        flash("Patient added successfully.", "success")

        return redirect(url_for("patients"))

    q = request.args.get("q", "").strip()

    if q:
        records = Patient.query.filter(
            Patient.name.ilike(f"%{q}%")
        ).order_by(Patient.id.desc()).all()
    else:
        records = Patient.query.order_by(
            Patient.id.desc()
        ).all()

    return render_template(
        "patients.html",
        records=records
    )


@app.route("/patients/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_patient(record_id):

    record = db.get_or_404(Patient, record_id)

    db.session.delete(record)
    db.session.commit()

    flash("Patient deleted.", "success")

    return redirect(url_for("patients"))


# --------------------------------------------------
# DOCTOR MANAGEMENT
# --------------------------------------------------

@app.route("/doctors", methods=["GET", "POST"])
@login_required
def doctors():

    if request.method == "POST":

        d = Doctor(
            name=request.form["name"].strip(),
            specialization=request.form["specialization"].strip(),
            phone=request.form["phone"].strip()
        )

        db.session.add(d)
        db.session.commit()

        flash("Doctor added successfully.", "success")

        return redirect(url_for("doctors"))

    records = Doctor.query.order_by(
        Doctor.id.desc()
    ).all()

    return render_template(
        "doctors.html",
        records=records
    )


@app.route("/doctors/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_doctor(record_id):

    record = db.get_or_404(Doctor, record_id)

    if record.appointments:

        flash(
            "This doctor has appointments. Remove or reassign them first.",
            "danger"
        )

    else:

        db.session.delete(record)
        db.session.commit()

        flash("Doctor deleted.", "success")

    return redirect(url_for("doctors"))


# --------------------------------------------------
# APPOINTMENT MANAGEMENT
# --------------------------------------------------

@app.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():

    if request.method == "POST":

        a = Appointment(
            patient_id=int(request.form["patient_id"]),
            doctor_id=int(request.form["doctor_id"]),
            appointment_date=date.fromisoformat(
                request.form["appointment_date"]
            ),
            appointment_time=request.form["appointment_time"],
            status=request.form["status"]
        )

        db.session.add(a)
        db.session.commit()

        flash("Appointment booked.", "success")

        return redirect(url_for("appointments"))

    records = Appointment.query.order_by(
        Appointment.appointment_date.desc()
    ).all()

    return render_template(
        "appointments.html",
        records=records,
        patients=Patient.query.all(),
        doctors=Doctor.query.all()
    )


@app.route("/appointments/<int:record_id>/status", methods=["POST"])
@login_required
def update_appointment(record_id):

    record = db.get_or_404(Appointment, record_id)

    record.status = request.form["status"]

    db.session.commit()

    flash("Appointment status updated.", "success")

    return redirect(url_for("appointments"))


# --------------------------------------------------
# PRESCRIPTION MANAGEMENT
# --------------------------------------------------

@app.route("/prescriptions", methods=["GET", "POST"])
@login_required
def prescriptions():

    if request.method == "POST":

        p = Prescription(
            appointment_id=int(request.form["appointment_id"]),
            diagnosis=request.form["diagnosis"].strip(),
            medicines=request.form["medicines"].strip(),
            notes=request.form.get("notes", "").strip()
        )

        db.session.add(p)
        db.session.commit()

        flash("Prescription saved.", "success")

        return redirect(url_for("prescriptions"))

    records = Prescription.query.order_by(
        Prescription.id.desc()
    ).all()

    used = [p.appointment_id for p in records]

    if used:
        available = Appointment.query.filter(
            ~Appointment.id.in_(used)
        ).all()
    else:
        available = Appointment.query.all()

    return render_template(
        "prescriptions.html",
        records=records,
        appointments=available
    )


# --------------------------------------------------
# BILLING MANAGEMENT
# --------------------------------------------------

@app.route("/billing", methods=["GET", "POST"])
@login_required
def billing():

    if request.method == "POST":

        b = Bill(
            appointment_id=int(request.form["appointment_id"]),
            amount=Decimal(request.form["amount"]),
            payment_status=request.form["payment_status"]
        )

        db.session.add(b)
        db.session.commit()

        flash("Bill created.", "success")

        return redirect(url_for("billing"))

    records = Bill.query.order_by(
        Bill.id.desc()
    ).all()

    used = [b.appointment_id for b in records]

    if used:
        available = Appointment.query.filter(
            ~Appointment.id.in_(used)
        ).all()
    else:
        available = Appointment.query.all()

    return render_template(
        "billing.html",
        records=records,
        appointments=available
    )


@app.route("/billing/<int:record_id>/payment", methods=["POST"])
@login_required
def update_payment(record_id):

    record = db.get_or_404(Bill, record_id)

    record.payment_status = request.form["payment_status"]

    db.session.commit()

    flash("Payment status updated.", "success")

    return redirect(url_for("billing"))


# --------------------------------------------------
# DATABASE INITIALIZATION COMMAND
# --------------------------------------------------

@app.cli.command("init-db")
def init_db():

    """Create all database tables and a demo admin account."""

    db.create_all()

    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123")

    existing_user = User.query.filter_by(
        username=admin_username
    ).first()

    if not existing_user:

        admin = User(
            username=admin_username,
            password_hash=generate_password_hash(admin_password)
        )

        db.session.add(admin)
        db.session.commit()

    print("Database initialized successfully.")
    print("Admin username:", admin_username)


# --------------------------------------------------
# LOCAL DEVELOPMENT
# --------------------------------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)

from flask import request, Blueprint, redirect, render_template, url_for, flash, abort, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from pariksha.auth.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
from pariksha.models import User, Student, Teacher
from pariksha.auth.utils import send_reset_email, send_verification_email
from pariksha import bcrypt, db
from urllib.parse import urlparse, urljoin
import requests

auth = Blueprint("auth", __name__, template_folder="templates", static_folder="static")

@auth.route("/register", methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        if current_user.student:
            return redirect(url_for('student.home'))
        else:
            return redirect(url_for('teacher.home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(name=form.name.data, email=form.email.data, password=hashed_password)
        if form.acc_type.data == "Student":
            student = Student(user=user)
            db.session.add(user)
            db.session.add(student)
        else:
            teacher = Teacher(user=user)
            db.session.add(user)
            db.session.add(teacher)
        db.session.commit()
        flash("Account created successfully!", 'success')
        login_user(user, remember=False)
        return redirect(url_for('student.home') if user.student else url_for('teacher.home'))
    return render_template("register.html", form=form, title="Register")

@auth.route("/api/register", methods=["POST"])
def api_register():
    if request.json:
        name = request.json.get('name')
        email = request.json.get('email')
        password = request.json.get('password')
        acc_type = request.json.get('acc_type')
        
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, password=hashed_password)
        
        if acc_type == "Student":
            student = Student(user=user)
            db.session.add(student)
        elif acc_type == "Teacher":
            teacher = Teacher(user=user)
            db.session.add(teacher)
        else:
            return jsonify({"error": "Invalid account type"}), 400

        db.session.add(user)
        db.session.commit()
        
        return jsonify({"message": "User registered successfully", "user_id": user.id}), 201

@auth.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('student.home') if current_user.student else url_for('teacher.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=False)
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('student.home') if user.student else url_for('teacher.home'))
        else:
            flash("Incorrect email or password. Please try again.", "danger")

    return render_template("login.html", form=form, title="Login")

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.welcome"))

@auth.route("/verify_account/<token>")
def verify(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash("The token has expired!", "warning")
        return redirect(url_for("auth.login"))
    user.verified = True
    db.session.commit()
    flash("Your account has been verified", "success")
    return redirect(url_for("auth.login"))

@auth.route("/reset_password", methods=["GET", "POST"])
def request_reset():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash(f"{form.email.data} is not registered for any account", "danger")
            return redirect(url_for('auth.request_reset'))
        send_reset_email(user)
        flash("An email has been sent with instructions to reset your password", "info")
        return redirect(url_for("auth.login"))
    return render_template("request_reset.html", title="Reset Password", form=form)

@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash("The token is invalid or has expired. Please try again.", "danger")
        return redirect(url_for("auth.request_reset"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user.password = hashed_password
        db.session.commit()
        flash("Your password has been updated", 'success')
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", title="Reset Password", form=form)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

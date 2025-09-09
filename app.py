import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import db, User, Module, Quiz, Challenge, Submission, ForumPost
from forms import LoginForm, RegisterForm, QuizForm, ChallengeForm, ForumForm
from config import Config

# -----------------------------
# FLASK APP SETUP
# -----------------------------
app = Flask(__name__)
app.config.from_object(Config)

# Initialize DB
db.init_app(app)

# Login manager setup
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Upload folder setup
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# -----------------------------
# LOGIN MANAGER
# -----------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Inject current datetime into templates
@app.context_processor
def inject_now():
    return {"now": datetime.now}

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    modules = Module.query.all()
    challenges = Challenge.query.all()
    top_users = User.query.order_by(User.eco_points.desc()).limit(5).all()
    return render_template(
        "index.html", modules=modules, challenges=challenges, top_users=top_users
    )

# ---------- AUTH ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(form.password.data)
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_pw,
            role=form.role.data or "student",
            eco_points=0,
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("index"))

# ---------- DASHBOARD ----------
@app.route("/dashboard")
@login_required
def dashboard():
    modules = Module.query.all()
    challenges = Challenge.query.all()

    if current_user.role == "teacher":
        return render_template(
            "dashboard_teacher.html",
            modules=modules,
            challenges=challenges,
        )

    leaderboard = User.query.filter_by(role="student").order_by(
        User.eco_points.desc()
    ).limit(5).all()

    return render_template(
        "dashboard_student.html",
        modules=modules,
        challenges=challenges,
        leaderboard=leaderboard,
    )

# ---------- MODULE DETAIL ----------
@app.route("/module/<int:module_id>")
@login_required
def module_detail(module_id):
    module_obj = Module.query.get_or_404(module_id)
    # TODO: You can add logic to check if the student has completed this module
    return render_template("module.html", module=module_obj)

# ---------- FORUM ----------
@app.route("/forum", methods=["GET", "POST"])
@login_required
def forum():
    form = ForumForm()
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    if form.validate_on_submit():
        post = ForumPost(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash("Post added!", "success")
        return redirect(url_for("forum"))
    return render_template("forum.html", form=form, posts=posts)

# ---------- CHALLENGES ----------
@app.route("/challenge/<int:challenge_id>", methods=["GET", "POST"])
@login_required
def challenge(challenge_id):
    challenge_obj = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm()
    if form.validate_on_submit():
        proof_file = request.files.get("proof_file")
        proof_link = None
        if proof_file and proof_file.filename:
            filename = secure_filename(proof_file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            proof_file.save(filepath)
            proof_link = filepath

        submission = Submission(
            user_id=current_user.id,
            challenge_id=challenge_obj.id,
            proof_link=proof_link,
            status="pending",
        )
        db.session.add(submission)
        db.session.commit()
        flash("Submission uploaded!", "success")
        return redirect(url_for("dashboard"))
    return render_template("challenge.html", form=form, challenge=challenge_obj)

# ---------- QUIZ ----------
@app.route("/quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def quiz(quiz_id):
    quiz_obj = Quiz.query.get_or_404(quiz_id)
    form = QuizForm()
    if form.validate_on_submit():
        answer = request.form.get("answer")
        if answer and answer.strip().lower() == quiz_obj.correct_answer.strip().lower():
            current_user.eco_points += quiz_obj.points or 10
            db.session.commit()
            flash(f"Correct! +{quiz_obj.points or 10} Eco Points", "success")
        else:
            flash("Incorrect, try again!", "danger")
        return redirect(url_for("dashboard"))
    return render_template("quiz.html", form=form, quiz=quiz_obj)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

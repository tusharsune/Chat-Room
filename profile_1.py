from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from database import db, User  # Import database and User model
import os

profile_bp = Blueprint('profile_bp', __name__)  # 🔹 Blueprint must match in `url_for`

UPLOAD_FOLDER = "static/images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload folder exists

@profile_bp.route('/')
@login_required
def profile():
    user = User.query.filter_by(username=current_user.username).first()

    # ✅ Fix: Ensure `profile_pic` is never None (Default: "default.png")
    profile_pic = user.profile_pic if user.profile_pic else "default.png"

    return render_template("profile.html", username=user.username, user=user, profile_pic=profile_pic)

@profile_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = User.query.filter_by(username=current_user.username).first()

    if request.method == 'POST':
        bio = request.form.get("bio")
        profile_pic = request.files.get("profile_pic")

        if bio:
            user.bio = bio  # Update bio in DB

        if profile_pic and profile_pic.filename:
            filename = f"{user.username}.png"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            profile_pic.save(filepath)
            user.profile_pic = filename  # Save filename in DB

        db.session.commit()  # Save changes

        return redirect(url_for('profile_bp.profile'))  # 🔹 Corrected blueprint name

    return render_template("edit_profile.html", user=user)

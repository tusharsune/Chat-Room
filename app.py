from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from database import db, User, Message  # ✅ Import Message model
from profile_1 import profile_bp  # Import blueprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Tushu'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Flask-Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ **Home Route**
@app.route('/')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first()  # Fetch user data
    return render_template('index.html', user=user, username=current_user.username)

# ✅ **Signup Route**
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return "Username already exists. Try another one!"

        # Create new user
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html')

# ✅ **Login Route**
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)  # Log in the user
            return redirect(url_for('home'))
        else:
            return "Invalid credentials!"

    return render_template('login.html')

# ✅ **Logout Route**
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ✅ **Chat Room Route**
@app.route('/chat/<room>', methods=['GET', 'POST'])
@login_required
def chat(room):
    if request.method == 'POST':
        content = request.form.get('message')
        if content:
            new_message = Message(user_id=current_user.id, room=room, content=content)
            db.session.add(new_message)
            db.session.commit()

    messages = Message.query.filter_by(room=room).order_by(Message.timestamp).all()
    return render_template('chat.html', room=room, messages=messages, username=current_user.username)

# ✅ **Delete Message Route**
@app.route('/delete/<int:message_id>/<room>', methods=['POST'])
@login_required
def delete_message(message_id, room):
    message = Message.query.get_or_404(message_id)

    if message.user_id != current_user.id:
        return "You are not allowed to delete this message!", 403

    db.session.delete(message)
    db.session.commit()
    return redirect(url_for('chat', room=room))

@app.route('/mini-profile/<username>/<room>')
def mini_profile(username, room):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('mini_profile.html', user=user, room=room)


# ✅ **Register Blueprints**
app.register_blueprint(profile_bp, url_prefix="/profile")

# ✅ **Run the App**
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure database tables are created
    app.run(debug=True)

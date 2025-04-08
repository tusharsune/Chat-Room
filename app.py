from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from database import db, User, Message  
from profile_1 import profile_bp  
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Tushu'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

socketio = SocketIO(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first()  
    return render_template('index.html', user=user, username=current_user.username)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        if User.query.filter_by(username=username).first():
            return "Username already exists. Try another one!"

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)  
            return redirect(url_for('home'))
        else:
            return "Invalid credentials!"

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat/<room>', methods=['GET'])
@login_required
def chat(room):
    messages = Message.query.filter_by(room=room).order_by(Message.timestamp).all()
    return render_template('chat.html', room=room, messages=messages, username=current_user.username)

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

@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = data['message']
    username = data['username']

    user = User.query.filter_by(username=username).first()
    if user:
        new_message = Message(user_id=user.id, room=room, content=message)
        db.session.add(new_message)
        db.session.commit()

        emit('receive_message', {
            'username': username,
            'message': message,
            'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }, room=room)
        return {'success': True}
    return {'success': False}

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('user_joined', {'username': username}, room=room)

app.register_blueprint(profile_bp, url_prefix="/profile")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)

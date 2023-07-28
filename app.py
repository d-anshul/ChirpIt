from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime  # Add this import
from flask_humanize import Humanize  # Add this import

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chirp.db'
db = SQLAlchemy(app)
humanize = Humanize(app)  # Initialize Humanize

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    chirps = db.relationship('Chirp', backref='user', lazy=True)


class Chirp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(280), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not (username and password):
            flash('Username and password are required.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose a different one.', 'error')
        else:
            new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
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
            return redirect(url_for('timeline'))
        else:
            flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html')


@app.route('/timeline', methods=['GET', 'POST'])
@login_required
def timeline():
    if request.method == 'POST':
        chirp_text = request.form['chirp_text']
        if chirp_text:
            new_chirp = Chirp(text=chirp_text, timestamp=datetime.utcnow(), user=current_user)
            db.session.add(new_chirp)
            db.session.commit()
            flash('Chirp posted successfully!', 'success')
            return redirect(url_for('timeline'))

    chirps = Chirp.query.order_by(Chirp.timestamp.desc()).all()
    return render_template('timeline.html', chirps=chirps)

@app.route('/user/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    chirps = Chirp.query.filter_by(user_id=user.id).order_by(Chirp.timestamp.desc()).all()
    return render_template('user_profile.html', user=user, chirps=chirps)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)

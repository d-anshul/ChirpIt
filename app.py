from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_humanize import Humanize
import arrow  # Add this import

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chirp.db'
db = SQLAlchemy(app)
humanize = Humanize(app)

# Add this function to register 'naturaltime' filter
def naturaltime(value):
    return arrow.get(value).humanize()

app.jinja_env.filters['naturaltime'] = naturaltime

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    chirps = db.relationship('Chirp', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)

class Chirp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(280), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='chirp', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(280), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chirp_id = db.Column(db.Integer, db.ForeignKey('chirp.id'), nullable=False)

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

@app.route('/chirp/<int:chirp_id>', methods=['GET', 'POST'])
@login_required
def chirp(chirp_id):
    chirp = Chirp.query.get_or_404(chirp_id)
    if request.method == 'POST':
        comment_text = request.form['comment_text']
        if comment_text:
            new_comment = Comment(text=comment_text, timestamp=datetime.utcnow(), user=current_user, chirp=chirp)
            db.session.add(new_comment)
            db.session.commit()
            flash('Your comment has been posted!', 'success')
            return redirect(url_for('chirp', chirp_id=chirp_id))
    return render_template('chirp.html', chirp=chirp)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    secret_answer_hash = db.Column(db.String(128))
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    emails = db.relationship('AnalyzedEmail', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_secret_answer(self, answer):
        self.secret_answer_hash = generate_password_hash(answer.lower().strip())

    def check_secret_answer(self, answer):
        return check_password_hash(self.secret_answer_hash, answer.lower().strip())

    def get_pending_count(self):
        return User.query.filter_by(is_verified=False).count()

class AnalyzedEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    email_id = db.Column(db.String(255), unique=True, nullable=False)
    sender = db.Column(db.String(255), nullable=True)
    subject = db.Column(db.String(255), nullable=True)
    result = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Float, nullable=False)
    content = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    risk_factors = db.Column(db.Text, nullable=True) 
    safety_score = db.Column(db.Text, nullable=True) 
    reasoning = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<AnalyzedEmail {self.email_id}>'

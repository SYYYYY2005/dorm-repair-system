from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, repairman, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RepairOrder(db.Model):
    __tablename__ = 'repair_orders'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    repairman_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    room_number = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(256), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed
    version = db.Column(db.Integer, default=1, nullable=False)  # 乐观锁
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    student = db.relationship('User', foreign_keys=[student_id], backref='repairs_submitted')
    repairman = db.relationship('User', foreign_keys=[repairman_id], backref='repairs_assigned')

class Evaluation(db.Model):
    __tablename__ = 'evaluations'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('repair_orders.id'), unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('score BETWEEN 1 AND 5', name='check_score_range'),
    )

    # 关系
    repair_order = db.relationship('RepairOrder', backref=db.backref('evaluation', uselist=False))
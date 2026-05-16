from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student/repairman/admin
class RepairOrder(db.Model):
    __tablename__ = 'repair_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    repairman_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    room_number = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed
    version = db.Column(db.Integer, default=1, nullable=False)  # 乐观锁版本号
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # 关系（可选）
    student = db.relationship('User', foreign_keys=[student_id], backref='repairs_submitted')
    repairman = db.relationship('User', foreign_keys=[repairman_id], backref='repairs_assigned')
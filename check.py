from models import db, User
from app import app
with app.app_context():
    user = User.query.filter_by(username='testuser').first()
    if user:
        print("找到用户:", user.username)
        print("存储的密码哈希:", user.password_hash)
    else:
        print("未找到用户")
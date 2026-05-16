import bcrypt
from models import db, User
from app import app

with app.app_context():
    user = User.query.filter_by(username='testuser').first()
    if user:
        stored_hash = user.password_hash.encode('utf-8')
        is_valid = bcrypt.checkpw("123456".encode('utf-8'), stored_hash)
        print("密码验证结果:", is_valid)   # 应为 True
    else:
        print("未找到用户")
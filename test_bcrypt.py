import bcrypt
from models import db, User
from app import app

with app.app_context():
    user = User.query.filter_by(username='testuser').first()
    if user:
        # 测试输入密码 "123456"
        is_correct = bcrypt.checkpw("123456".encode('utf-8'), user.password_hash.encode('utf-8'))
        print("密码验证结果:", is_correct)   # 应为 True
    else:
        print("用户不存在")
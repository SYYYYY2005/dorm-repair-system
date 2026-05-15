import bcrypt
from flask import Blueprint, request, jsonify
from models import db, User
from flask_jwt_extended import create_access_token
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student')

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "用户名或邮箱已注册"}), 400
    if len(password) < 6 or len(password) > 20:
        return jsonify({"error": "密码长度应为6-20位"}), 400

    # 加密密码
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    new_user = User(username=username, password_hash=hashed.decode('utf-8'), role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "注册成功"}), 201
from flask_jwt_extended import create_access_token   # 放在文件顶部

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    from models import User   # 如果顶部已经导入，则不需要重复
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "用户名或密码错误"}), 401

    # 验证密码
    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({"error": "用户名或密码错误"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({
        "access_token": access_token,
        "user_id": user.id,
        "role": user.role
    }), 200
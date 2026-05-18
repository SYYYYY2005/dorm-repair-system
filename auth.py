from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import db, User
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student')   # 获取 role，默认为 student

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "用户名已存在"}), 400

    # 可选：限制 role 取值
    if role not in ['student', 'repairman', 'admin']:
        return jsonify({"error": "无效的角色"}), 400

    # 密码加密
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    # ★ 修改点：创建用户时传入 role 参数 ★
    new_user = User(username=username, password_hash=hashed.decode('utf-8'), role=role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "用户名或密码错误"}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({"error": "用户名或密码错误"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": access_token,
        "user_id": user.id,
        "role": user.role
    }), 200
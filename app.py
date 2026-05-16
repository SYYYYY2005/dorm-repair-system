from services import RepairService
from flask import Flask, request, jsonify
from config import Config
from flask_jwt_extended import jwt_required, JWTManager, get_jwt_identity
from models import db
from auth import auth_bp

# 添加 api_response 函数
def api_response(data=None, message="", code=200, error=None):
    """统一响应格式"""
    if error:
        return jsonify({"error": error}), code
    return jsonify({"data": data, "message": message}), code

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)
app.register_blueprint(auth_bp)

@app.route('/api/repairs', methods=['POST'])
@jwt_required()
def create_repair():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    order, error = RepairService.create_repair(current_user_id, data)
    if error:
        return api_response(code=400, error=error)
    return api_response(data={"id": order.id}, message="报修单已提交", code=201)

@app.route('/api/repairs', methods=['GET'])
@jwt_required()
def get_repairs():
    current_user_id = get_jwt_identity()
    orders = RepairService.get_repairs_by_student(current_user_id)
    result = [{"id": o.id, "room": o.room_number, "desc": o.description, "status": o.status, "created_at": o.created_at.isoformat()} for o in orders]
    return api_response(data=result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
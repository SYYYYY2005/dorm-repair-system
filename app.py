from flask import Flask, request
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from auth import auth_bp
from services import RepairService
from utils import api_response, jwt_required

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)

# 注册蓝图（用户模块）
app.register_blueprint(auth_bp)

# ==================== 报修模块 ====================

@app.route('/api/repairs', methods=['POST'])
@jwt_required
def create_repair():
    from flask_jwt_extended import get_jwt_identity
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        order, error = RepairService.create_repair(current_user_id, data)
        if error:
            return api_response(code=400, error=error)
        return api_response(data={"id": order.id}, message="报修单已提交", code=201)
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"创建报修单失败: {e}")
        return api_response(code=500, error="系统繁忙，请稍后重试")

@app.route('/api/repairs', methods=['GET'])
@jwt_required
def get_repairs():
    from flask_jwt_extended import get_jwt_identity
    current_user_id = int(get_jwt_identity())
    try:
        orders = RepairService.get_repairs_by_student(current_user_id)
        result = [{
            "id": o.id,
            "room": o.room_number,
            "description": o.description,
            "status": o.status,
            "created_at": o.created_at.isoformat()
        } for o in orders]
        return api_response(data=result)
    except Exception as e:
        app.logger.error(f"获取报修列表失败: {e}")
        return api_response(code=500, error="系统繁忙，请稍后重试")

# ==================== 错误处理 ====================
@app.errorhandler(404)
def not_found(e):
    return api_response(code=404, error="资源不存在")

@app.errorhandler(500)
def internal_error(e):
    return api_response(code=500, error="服务器内部错误")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
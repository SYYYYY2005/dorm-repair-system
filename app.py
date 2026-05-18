from flask import Flask, request, send_from_directory
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from auth import auth_bp
from services import RepairService, EvaluationService
from utils import api_response, jwt_required

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)

# 注册蓝图（用户模块）
app.register_blueprint(auth_bp)

# ==================== 前端静态文件服务 ====================
@app.route('/')
def index():
    return send_from_directory('frontend', 'login.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('frontend', filename)

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
    from models import Evaluation
    current_user_id = int(get_jwt_identity())
    try:
        orders = RepairService.get_repairs_by_student(current_user_id)
        result = []
        for o in orders:
            evaluation = Evaluation.query.filter_by(order_id=o.id).first()
            eval_data = None
            if evaluation:
                eval_data = {"score": evaluation.score, "comment": evaluation.comment}
            result.append({
                "id": o.id,
                "room": o.room_number,
                "description": o.description,
                "status": o.status,
                "repairman_id": o.repairman_id,
                "evaluation": eval_data,
                "created_at": o.created_at.isoformat()
            })
        return api_response(data=result)
    except Exception as e:
        app.logger.error(f"获取报修列表失败: {e}")
        return api_response(code=500, error="系统繁忙，请稍后重试")

# ==================== 工单模块 ====================
@app.route('/api/repairs/assigned', methods=['GET'])
@jwt_required
def get_assigned_repairs():
    from flask_jwt_extended import get_jwt_identity
    from models import User, Evaluation
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role != 'repairman':
        return api_response(code=403, error="权限不足")
    orders = RepairService.get_repairs_for_repairman(current_user_id)
    result = []
    for o in orders:
        evaluation = Evaluation.query.filter_by(order_id=o.id).first()
        eval_data = None
        if evaluation:
            eval_data = {"score": evaluation.score, "comment": evaluation.comment}
        result.append({
            "id": o.id,
            "room": o.room_number,
            "description": o.description,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
            "evaluation": eval_data
        })
    return api_response(data=result)

@app.route('/api/repairs/all', methods=['GET'])
@jwt_required
def get_all_repairs():
    from flask_jwt_extended import get_jwt_identity
    from models import User, Evaluation
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return api_response(code=403, error="权限不足")
    status = request.args.get('status')
    orders = RepairService.get_all_repairs(status)
    result = []
    for o in orders:
        evaluation = Evaluation.query.filter_by(order_id=o.id).first()
        eval_data = None
        if evaluation:
            eval_data = {"score": evaluation.score, "comment": evaluation.comment}
        result.append({
            "id": o.id,
            "student_id": o.student_id,
            "room": o.room_number,
            "description": o.description,
            "status": o.status,
            "repairman_id": o.repairman_id,
            "evaluation": eval_data,
            "created_at": o.created_at.isoformat()
        })
    return api_response(data=result)

@app.route('/api/repairs/<int:order_id>/status', methods=['PUT'])
@jwt_required
def update_repair_status(order_id):
    from flask_jwt_extended import get_jwt_identity
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    new_status = data.get('status')
    if not new_status:
        return api_response(code=400, error="缺少status字段")
    if new_status not in ['processing', 'completed']:
        return api_response(code=400, error="无效状态值，只允许 processing 或 completed")
    from models import User
    user = User.query.get(current_user_id)
    if not user or user.role != 'repairman':
        return api_response(code=403, error="权限不足")
    order, error = RepairService.update_repair_status(order_id, current_user_id, new_status)
    if error:
        return api_response(code=400, error=error)
    return api_response(message="状态更新成功")

@app.route('/api/repairs/<int:order_id>/assign', methods=['PUT'])
@jwt_required
def assign_repair_order(order_id):
    from flask_jwt_extended import get_jwt_identity
    from models import User, RepairOrder
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    repairman_id = data.get('repairman_id')
    if not repairman_id:
        return api_response(code=400, error="缺少repairman_id")
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return api_response(code=403, error="权限不足")
    order, error = RepairService.assign_repair_order(order_id, current_user_id, repairman_id)
    if error:
        return api_response(code=400, error=error)
    # 分配成功后，将工单状态改为 processing
    order_obj = RepairOrder.query.get(order_id)
    if order_obj and order_obj.status == 'pending':
        order_obj.status = 'processing'
        db.session.commit()
    return api_response(message="分配成功")

# ==================== 评价模块 ====================
@app.route('/api/repairs/<int:order_id>/evaluation', methods=['POST'])
@jwt_required
def create_evaluation(order_id):
    from flask_jwt_extended import get_jwt_identity
    from models import User
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role != 'student':
        return api_response(code=403, error="只有学生可以评价")
    data = request.get_json()
    eval_obj, error = EvaluationService.create_evaluation(order_id, current_user_id, data)
    if error:
        return api_response(code=400, error=error)
    return api_response(data={"id": eval_obj.id}, message="评价成功", code=201)

# ==================== 辅助接口：获取所有维修工 ====================
@app.route('/api/users/repairmen', methods=['GET'])
@jwt_required
def get_repairmen():
    from models import User
    from flask_jwt_extended import get_jwt_identity
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return api_response(code=403, error="权限不足")
    repairmen = User.query.filter_by(role='repairman').all()
    data = [{"id": r.id, "username": r.username} for r in repairmen]
    return api_response(data=data)

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
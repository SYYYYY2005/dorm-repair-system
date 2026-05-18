import re
import logging
from models import RepairOrder, Evaluation
from repositories import RepairOrderRepository, UserRepository, EvaluationRepository

# 配置日志
logging.basicConfig(level=logging.INFO)

class RepairService:
    # 允许的状态转换映射
    ALLOWED_STATUS_TRANSITIONS = {
        'pending': ['processing'],
        'processing': ['completed'],
        'completed': []   # 已完成不可再转
    }
    
    # ========== 报修模块已有方法 ==========
    @staticmethod
    def create_repair(student_id, data):
        room = data.get('room_number')
        desc = data.get('description')
        if not room or not desc:
            return None, "房间号和故障描述不能为空"
        if not re.match(r'^\d{3}$', room):
            return None, "房间号必须为三位数字"
        user = UserRepository.get_by_id(student_id)
        if not user or user.role != 'student':
            return None, "只有学生可以提交报修单"
        order = RepairOrder(
            student_id=student_id,
            room_number=room,
            description=desc,
            image_url=data.get('image_url'),
            status='pending'
        )
        return RepairOrderRepository.add(order), None

    @staticmethod
    def get_repairs_by_student(student_id):
        return RepairOrderRepository.get_by_student(student_id)

    # ========== 工单模块新增方法 ==========
    @staticmethod
    def get_repairs_for_repairman(repairman_id):
        return RepairOrderRepository.get_by_repairman(repairman_id)

    @staticmethod
    def get_all_repairs(status=None):
        return RepairOrderRepository.get_all(status)

    @staticmethod
    def update_repair_status(order_id, repairman_id, new_status):
        # 获取工单并保存当前版本号（乐观锁）
        order = RepairOrderRepository.get_by_id(order_id, repairman_id=repairman_id)
        if not order:
            return None, "工单不存在或无权操作"
        
        # 保存当前版本号
        current_version = order.version
        
        # 增加状态转换校验
        allowed_next = RepairService.ALLOWED_STATUS_TRANSITIONS.get(order.status, [])
        if new_status not in allowed_next:
            return None, f"不允许从 {order.status} 直接变更为 {new_status}"
        
        # 更新状态，传入版本号
        old_status = order.status
        order = RepairOrderRepository.update_status(order_id, new_status, version=current_version)
        
        # 检查是否因版本冲突而失败
        if order is None:
            return None, "更新失败，工单已被其他操作修改，请重试"
        
        # 记录日志
        logging.info(f"维修工 {repairman_id} 将工单 {order_id} 状态从 {old_status} 变更为 {new_status}")
        
        return order, None

    @staticmethod
    def assign_repair_order(order_id, admin_id, repairman_id):
        order = RepairOrder.query.get(order_id)
        if not order:
            return None, "工单不存在"
        
        # 增加：检查工单是否已分配
        if order.repairman_id is not None:
            return None, "该工单已被分配，无法重复分配"
        
        from repositories import UserRepository
        repairman = UserRepository.get_by_id(repairman_id)
        if not repairman or repairman.role != 'repairman':
            return None, "指定的用户不是维修工"
        
        old_repairman_id = order.repairman_id
        order = RepairOrderRepository.assign_repairman(order_id, repairman_id)
        
        # 记录分配日志
        logging.info(f"管理员 {admin_id} 将工单 {order_id} 分配给维修工 {repairman_id}（原维修工: {old_repairman_id}）")
        
        return order, None


# ========== 新增：评价模块 Service ==========
class EvaluationService:
    @staticmethod
    def create_evaluation(order_id, student_id, data):
        from models import RepairOrder
        order = RepairOrder.query.get(order_id)
        if not order or order.student_id != student_id:
            return None, "工单不存在或无权限"
        if order.status != 'completed':
            return None, "只有已完成的工单才能评价"
        if Evaluation.query.filter_by(order_id=order_id).first():
            return None, "该工单已评价过"
        score = data.get('score')
        if not isinstance(score, int) or score < 1 or score > 5:
            return None, "评分必须是1-5之间的整数"
        comment = data.get('comment', '')
        evaluation = Evaluation(order_id=order_id, score=score, comment=comment)
        return EvaluationRepository.add(evaluation), None
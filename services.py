import re
from models import RepairOrder
from repositories import RepairOrderRepository, UserRepository

class RepairService:
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
        order = RepairOrderRepository.get_by_id(order_id, repairman_id=repairman_id)
        if not order:
            return None, "工单不存在或无权操作"
        if new_status not in ['processing', 'completed']:
            return None, "无效的状态变更"
        if order.status == 'completed':
            return None, "工单已完成，无法修改"
        order = RepairOrderRepository.update_status(order_id, new_status)
        return order, None

    @staticmethod
    def assign_repair_order(order_id, admin_id, repairman_id):
        order = RepairOrder.query.get(order_id)
        if not order:
            return None, "工单不存在"
        repairman = UserRepository.get_by_id(repairman_id)
        if not repairman or repairman.role != 'repairman':
            return None, "指定的用户不是维修工"
        order = RepairOrderRepository.assign_repairman(order_id, repairman_id)
        return order, None
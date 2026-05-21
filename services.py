import re
from models import RepairOrder, User, Evaluation
from repositories import RepairOrderRepository, UserRepository, EvaluationRepository

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
        if order.repairman_id is not None:
            return None, "该工单已被分配，无法重复分配"
        repairman = UserRepository.get_by_id(repairman_id)
        if not repairman or repairman.role != 'repairman':
            return None, "指定的用户不是维修工"
        order = RepairOrderRepository.assign_repairman(order_id, repairman_id)
        return order, None

class EvaluationService:
    @staticmethod
    def create_evaluation(order_id, student_id, data):
        # 1. 检查工单是否存在
        order = RepairOrder.query.get(order_id)
        if not order:
            return None, "工单不存在"

        # 2. 检查工单是否属于该学生
        if order.student_id != student_id:
            return None, "无权评价此工单"

        # 3. 检查工单状态
        if order.status != 'completed':
            return None, "只有已完成的工单才能评价"

        # 4. 检查是否已评价过
        if Evaluation.query.filter_by(order_id=order_id).first():
            return None, "该工单已评价过"

        # 5. 校验评分
        score = data.get('score')
        if not isinstance(score, int) or score < 1 or score > 5:
            return None, "评分必须为 1-5 之间的整数"

        comment = data.get('comment', '')

        evaluation = Evaluation(
            order_id=order_id,
            score=score,
            comment=comment
        )
        return EvaluationRepository.add(evaluation), None
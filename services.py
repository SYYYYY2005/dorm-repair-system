import re
from models import RepairOrder
from repositories import RepairOrderRepository, UserRepository

class RepairService:
    @staticmethod
    def create_repair(student_id, data):
        room = data.get('room_number')
        desc = data.get('description')
        if not room or not desc:
            return None, "房间号和故障描述不能为空"

        # 房间号格式校验（三位数字）
        if not re.match(r'^\d{3}$', room):
            return None, "房间号必须为三位数字"

        # 检查当前用户是否为 student 角色
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
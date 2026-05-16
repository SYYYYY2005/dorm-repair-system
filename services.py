from repositories import RepairOrderRepository
from models import RepairOrder

class RepairService:
    @staticmethod
    def create_repair(student_id, data):
        room = data.get('room_number')
        desc = data.get('description')
        if not room or not desc:
            return None, "房间号和故障描述不能为空"
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
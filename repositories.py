from models import db, RepairOrder

class RepairOrderRepository:
    @staticmethod
    def add(order):
        db.session.add(order)
        db.session.commit()
        return order

    @staticmethod
    def get_by_student(student_id):
        return RepairOrder.query.filter_by(student_id=student_id).order_by(RepairOrder.created_at.desc()).all()

    @staticmethod
    def get_by_id(order_id, student_id=None, repairman_id=None):
        query = RepairOrder.query.filter_by(id=order_id)
        if student_id:
            query = query.filter_by(student_id=student_id)
        if repairman_id:
            query = query.filter_by(repairman_id=repairman_id)
        return query.first()
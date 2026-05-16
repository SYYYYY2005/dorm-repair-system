from models import db, User, RepairOrder

class UserRepository:
    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def add(user):
        db.session.add(user)
        db.session.commit()
        return user

class RepairOrderRepository:
    # ========== 报修模块已有方法 ==========
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

    # ========== 工单模块新增方法 ==========
    @staticmethod
    def get_by_repairman(repairman_id):
        return RepairOrder.query.filter_by(repairman_id=repairman_id).order_by(RepairOrder.created_at.desc()).all()

    @staticmethod
    def get_all(status=None):
        query = RepairOrder.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(RepairOrder.created_at.desc()).all()

    @staticmethod
    def update_status(order_id, new_status):
        order = RepairOrder.query.get(order_id)
        if order:
            order.status = new_status
            db.session.commit()
        return order

    @staticmethod
    def assign_repairman(order_id, repairman_id):
        order = RepairOrder.query.get(order_id)
        if order:
            order.repairman_id = repairman_id
            db.session.commit()
        return order
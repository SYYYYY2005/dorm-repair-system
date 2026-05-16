import pytest
from app import app, db
from models import User, RepairOrder, Evaluation

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
        db.drop_all()

def test_full_flow(client):
    # 1. 注册学生、维修工、管理员
    client.post('/api/register', json={'username':'stu','password':'123','role':'student'})
    client.post('/api/register', json={'username':'rep','password':'123','role':'repairman'})
    client.post('/api/register', json={'username':'adm','password':'123','role':'admin'})

    # 2. 学生登录
    res = client.post('/api/login', json={'username':'stu','password':'123'})
    stu_token = res.json['access_token']

    # 3. 提交报修单
    res = client.post('/api/repairs', headers={'Authorization': f'Bearer {stu_token}'}, json={'room_number':'101','description':'灯坏了'})
    order_id = res.json['data']['id']

    # 4. 管理员登录，分配工单给维修工（需要先获取维修工ID）
    res = client.post('/api/login', json={'username':'adm','password':'123'})
    adm_token = res.json['access_token']
    repairman = User.query.filter_by(username='rep').first()
    client.put(f'/api/repairs/{order_id}/assign', headers={'Authorization': f'Bearer {adm_token}'}, json={'repairman_id': repairman.id})

    # 5. 维修工登录，更新状态为 completed
    res = client.post('/api/login', json={'username':'rep','password':'123'})
    rep_token = res.json['access_token']
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, json={'status':'processing'})
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, json={'status':'completed'})

    # 6. 学生评价
    res = client.post(f'/api/repairs/{order_id}/evaluation', headers={'Authorization': f'Bearer {stu_token}'}, json={'score':5,'comment':'很好'})
    assert res.status_code == 201

    # 7. 验证评价已创建
    eval_obj = Evaluation.query.filter_by(order_id=order_id).first()
    assert eval_obj is not None
    assert eval_obj.score == 5
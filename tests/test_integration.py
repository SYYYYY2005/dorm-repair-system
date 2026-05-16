import sys
import os
# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app, db
from models import User, RepairOrder, Evaluation

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
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
    res = client.post('/api/repairs', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'room_number':'101','description':'灯坏了'})
    order_id = res.json['data']['id']

    # 4. 管理员登录，分配工单给维修工
    res = client.post('/api/login', json={'username':'adm','password':'123'})
    adm_token = res.json['access_token']
    repairman = User.query.filter_by(username='rep').first()
    client.put(f'/api/repairs/{order_id}/assign', headers={'Authorization': f'Bearer {adm_token}'}, 
               json={'repairman_id': repairman.id})

    # 5. 维修工登录，更新状态为 completed
    res = client.post('/api/login', json={'username':'rep','password':'123'})
    rep_token = res.json['access_token']
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'processing'})
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'completed'})

    # 6. 学生评价
    res = client.post(f'/api/repairs/{order_id}/evaluation', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'score':5,'comment':'很好'})
    assert res.status_code == 201

    # 7. 验证评价已创建
    eval_obj = Evaluation.query.filter_by(order_id=order_id).first()
    assert eval_obj is not None
    assert eval_obj.score == 5


def test_permission_denied(client):
    # 注册学生和维修工
    client.post('/api/register', json={'username':'stu2','password':'123','role':'student'})
    client.post('/api/register', json={'username':'rep2','password':'123','role':'repairman'})

    # 学生登录，提交报修单
    res = client.post('/api/login', json={'username':'stu2','password':'123'})
    stu_token = res.json['access_token']
    res = client.post('/api/repairs', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'room_number':'102','description':'漏水'})
    order_id = res.json['data']['id']

    # 维修工尝试分配工单（应返回 403 权限不足）
    res = client.post('/api/login', json={'username':'rep2','password':'123'})
    rep_token = res.json['access_token']
    res = client.put(f'/api/repairs/{order_id}/assign', headers={'Authorization': f'Bearer {rep_token}'}, 
                     json={'repairman_id': 999})
    assert res.status_code == 403

    # 学生尝试更新工单状态（应返回 403）
    res = client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {stu_token}'}, 
                     json={'status':'processing'})
    assert res.status_code == 403


def test_duplicate_evaluation(client):
    # 注册完整角色并完成一个工单
    client.post('/api/register', json={'username':'stu3','password':'123','role':'student'})
    client.post('/api/register', json={'username':'rep3','password':'123','role':'repairman'})
    client.post('/api/register', json={'username':'adm3','password':'123','role':'admin'})

    res = client.post('/api/login', json={'username':'stu3','password':'123'})
    stu_token = res.json['access_token']
    res = client.post('/api/repairs', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'room_number':'103','description':'问题'})
    order_id = res.json['data']['id']

    res = client.post('/api/login', json={'username':'adm3','password':'123'})
    adm_token = res.json['access_token']
    repairman = User.query.filter_by(username='rep3').first()
    client.put(f'/api/repairs/{order_id}/assign', headers={'Authorization': f'Bearer {adm_token}'}, 
               json={'repairman_id': repairman.id})

    res = client.post('/api/login', json={'username':'rep3','password':'123'})
    rep_token = res.json['access_token']
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'processing'})
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'completed'})

    # 第一次评价成功
    res = client.post(f'/api/repairs/{order_id}/evaluation', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'score':5,'comment':'good'})
    assert res.status_code == 201

    # 第二次评价应失败（400 或 409）
    res = client.post(f'/api/repairs/{order_id}/evaluation', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'score':4,'comment':'again'})
    assert res.status_code == 400
    assert '已评价' in res.json['error']
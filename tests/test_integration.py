import pytest
import os
import bcrypt
from app import app, db
from models import User, RepairOrder, Evaluation

@pytest.fixture
def client():
    # 使用测试专用的数据库文件
    test_db_path = 'test.db'
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{test_db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # 创建测试用户
            hashed = bcrypt.hashpw('123456'.encode('utf-8'), bcrypt.gensalt())
            student = User(username='stu', password_hash=hashed.decode('utf-8'), role='student')
            repairman = User(username='rep', password_hash=hashed.decode('utf-8'), role='repairman')
            admin = User(username='adm', password_hash=hashed.decode('utf-8'), role='admin')
            db.session.add_all([student, repairman, admin])
            db.session.commit()
            
            yield client
            
            db.session.remove()
            db.drop_all()
    
    # 删除测试数据库文件
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


def test_full_flow(client):
    """测试完整正常流程：登录 → 提交报修 → 分配 → 处理 → 评价"""
    # 1. 学生登录
    res = client.post('/api/login', json={'username':'stu','password':'123456'})
    assert 'access_token' in res.json
    stu_token = res.json['access_token']

    # 2. 提交报修单
    res = client.post('/api/repairs', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'room_number':'101','description':'灯坏了'})
    order_id = res.json['data']['id']

    # 3. 管理员登录，分配工单给维修工
    res = client.post('/api/login', json={'username':'adm','password':'123456'})
    adm_token = res.json['access_token']
    repairman = User.query.filter_by(username='rep').first()
    client.put(f'/api/repairs/{order_id}/assign', headers={'Authorization': f'Bearer {adm_token}'}, 
               json={'repairman_id': repairman.id})

    # 4. 维修工登录，更新状态为 completed
    res = client.post('/api/login', json={'username':'rep','password':'123456'})
    rep_token = res.json['access_token']
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'processing'})
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'completed'})

    # 5. 学生评价
    res = client.post(f'/api/repairs/{order_id}/evaluation', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'score':5,'comment':'很好'})
    assert res.status_code == 201

    # 6. 验证评价已创建
    eval_obj = Evaluation.query.filter_by(order_id=order_id).first()
    assert eval_obj is not None
    assert eval_obj.score == 5


def test_permission_denied(client):
    """测试越权操作"""
    # 1. 学生登录
    res = client.post('/api/login', json={'username':'stu','password':'123456'})
    stu_token = res.json['access_token']
    
    # 2. 学生登录，提交报修单
    res = client.post('/api/repairs', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'room_number':'102','description':'漏水'})
    order_id = res.json['data']['id']

    # 3. 维修工登录（不是管理员，尝试分配工单，应返回 403）
    res = client.post('/api/login', json={'username':'rep','password':'123456'})
    rep_token = res.json['access_token']
    res = client.put(f'/api/repairs/{order_id}/assign', headers={'Authorization': f'Bearer {rep_token}'}, 
                     json={'repairman_id': 999})
    assert res.status_code == 403

    # 4. 学生尝试更新工单状态（只有维修工可以，应返回 403）
    res = client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {stu_token}'}, 
                     json={'status':'processing'})
    assert res.status_code == 403


def test_duplicate_evaluation(client):
    """测试重复评价"""
    # 1. 学生登录
    res = client.post('/api/login', json={'username':'stu','password':'123456'})
    stu_token = res.json['access_token']
    
    # 2. 提交报修单
    res = client.post('/api/repairs', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'room_number':'103','description':'问题'})
    order_id = res.json['data']['id']

    # 3. 管理员分配
    res = client.post('/api/login', json={'username':'adm','password':'123456'})
    adm_token = res.json['access_token']
    repairman = User.query.filter_by(username='rep').first()
    client.put(f'/api/repairs/{order_id}/assign', headers={'Authorization': f'Bearer {adm_token}'}, 
               json={'repairman_id': repairman.id})

    # 4. 维修工完成
    res = client.post('/api/login', json={'username':'rep','password':'123456'})
    rep_token = res.json['access_token']
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'processing'})
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'completed'})

    # 5. 第一次评价成功
    res = client.post(f'/api/repairs/{order_id}/evaluation', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'score':5,'comment':'good'})
    assert res.status_code == 201

    # 6. 第二次评价应失败
    res = client.post(f'/api/repairs/{order_id}/evaluation', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'score':4,'comment':'again'})
    assert res.status_code == 400
    assert '已评价' in res.json['error']


def test_evaluation_negative_score(client):
    """测试边界值：负数评分"""
    from models import User

    # 1. 注册学生、维修工、管理员
    client.post('/api/register', json={'username':'stu2','password':'123','role':'student'})
    client.post('/api/register', json={'username':'rep2','password':'123','role':'repairman'})
    client.post('/api/register', json={'username':'adm2','password':'123','role':'admin'})

    # 2. 学生登录
    res = client.post('/api/login', json={'username':'stu2','password':'123'})
    assert res.status_code == 200
    stu_token = res.json['access_token']

    # 3. 提交报修单
    res = client.post('/api/repairs', headers={'Authorization': f'Bearer {stu_token}'}, 
                      json={'room_number':'101','description':'灯坏了'})
    assert res.status_code == 201
    order_id = res.json['data']['id']

    # 4. 管理员登录，分配工单
    res = client.post('/api/login', json={'username':'adm2','password':'123'})
    adm_token = res.json['access_token']
    repairman = User.query.filter_by(username='rep2').first()
    client.put(f'/api/repairs/{order_id}/assign', headers={'Authorization': f'Bearer {adm_token}'}, 
               json={'repairman_id': repairman.id})

    # 5. 维修工登录，更新状态为 completed
    res = client.post('/api/login', json={'username':'rep2','password':'123'})
    rep_token = res.json['access_token']
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'processing'})
    client.put(f'/api/repairs/{order_id}/status', headers={'Authorization': f'Bearer {rep_token}'}, 
               json={'status':'completed'})

    # 6. 学生尝试评价，评分为负数
    res = client.post(f'/api/repairs/{order_id}/evaluation', 
                      headers={'Authorization': f'Bearer {stu_token}'},
                      json={'score': -1, 'comment': 'bad'})
    # 预期应返回 400 错误（评分无效）
    assert res.status_code == 400
    assert '评分' in res.json.get('error', '') and ('1-5' in res.json.get('error', '') or '必须' in res.json.get('error', ''))


def test_evaluation_nonexistent_order(client):
    """测试评价不存在的工单"""
    # 1. 注册学生
    client.post('/api/register', json={'username':'stu4','password':'123','role':'student'})
    
    # 2. 学生登录
    res = client.post('/api/login', json={'username':'stu4','password':'123'})
    assert res.status_code == 200
    token = res.json['access_token']
    
    # 3. 尝试评价不存在的工单（id=99999）
    res = client.post('/api/repairs/99999/evaluation', 
                      headers={'Authorization': f'Bearer {token}'},
                      json={'score': 5, 'comment': 'good'})
    assert res.status_code in [400, 404]
    assert '不存在' in res.json.get('error', '')
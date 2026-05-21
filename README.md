# dorm-repair-system

宿舍报修系统 - 人人结对项目

系统部署说明



学号	                        姓名

233401010105	申玥

233401010102	张海璐

项目地址	https://github.com/SYYYYY2005/dorm-repair-system



技术栈声明

后端：Python 3.9+ + Flask + Flask-SQLAlchemy + Flask-JWT-Extended + bcrypt

前端：HTML5 + CSS3 + Bootstrap 5 + Font Awesome

数据库：SQLite（开发） / MySQL（生产）



本地部署步骤

1\. 克隆仓库

git clone https://github.com/SYYYYY2005/dorm-repair-system.git

cd dorm-repair-system

2\. 创建虚拟环境并安装依赖

python -m venv venv

\# Windows: venv\\Scripts\\activate

\# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt

3\. 初始化数据库

flask shell

>>> from models import db

>>> db.create\_all()

>>> exit()

4.启动后端服务

python app.py

后端运行在 http://127.0.0.1:5000

5\. 访问前端

打开浏览器，访问 http://127.0.0.1:5000 即可看到登录页面。

测试账号

学生：student1 / 123456

维修工：repair1 / 123456

管理员：admin1 / 123456

功能说明

学生：

提交报修单、查看我的报修单、对已完成工单评价。

维修工：

查看被分配的工单、更新工单状态（处理中/已完成）、查看学生评价。

管理员：

查看所有工单、分配工单给维修工（下拉选择维修工）、导出工单列表为 CSV。


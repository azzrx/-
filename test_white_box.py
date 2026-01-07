"""
白盒测试用例
核心模块：认证、学生管理、选课管理
"""
import pytest
import json
from datetime import datetime
import hashlib
from app import app
from database import init_db, get_db
import os
import sqlite3


@pytest.fixture
def client():
    """创建测试客户端"""
    # 使用测试数据库
    os.environ['DATABASE'] = 'test_student_management.db'
    
    app.config['TESTING'] = True
    
    # 初始化测试数据库
    init_db()
    
    with app.test_client() as client:
        yield client
    
    # 清理测试数据库
    if os.path.exists('test_student_management.db'):
        os.remove('test_student_management.db')


@pytest.fixture
def db():
    """创建数据库连接"""
    conn = get_db()
    yield conn
    conn.close()


class TestLoginModule:
    """测试认证模块 - login() 方法"""
    
    def test_login_successful_existing_user(self, client):
        """测试1：用户存在且密码正确的登录"""
        # Arrange: 使用默认用户admin
        response = client.post('/api/login', 
            json={'username': 'admin', 'password': 'admin123'})
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['username'] == 'admin'
        assert data['user']['role'] == 'admin'
    
    def test_login_auto_create_user_with_default_password(self, client):
        """测试2：不存在的用户，密码为默认值123456时自动创建"""
        # Arrange
        response = client.post('/api/login',
            json={'username': 'newstudent', 'password': '123456'})
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['username'] == 'newstudent'
        assert data['user']['role'] == 'student'  # 新建用户角色为学生
        assert 'student_id' in data['user']
    
    def test_login_auto_create_creates_student_record(self, client, db):
        """测试3：自动创建用户时，同时创建学生记录"""
        # Arrange & Act
        response = client.post('/api/login',
            json={'username': 'auto_user', 'password': '123456'})
        
        # Assert
        assert response.status_code == 200
        
        # 验证students表中是否存在对应记录
        cursor = db.cursor()
        cursor.execute('SELECT * FROM students WHERE student_id = ?', ('auto_user',))
        student = cursor.fetchone()
        assert student is not None
        assert student['name'] == 'auto_user'
    
    def test_login_existing_user_wrong_password(self, client):
        """测试4：用户存在但密码错误"""
        # Arrange
        response = client.post('/api/login',
            json={'username': 'admin', 'password': 'wrongpassword'})
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == False
        assert '用户名或密码错误' in data['message']
    
    def test_login_non_default_password_user_not_exist(self, client):
        """测试5：用户不存在且密码不是默认密码，不自动创建"""
        # Arrange
        response = client.post('/api/login',
            json={'username': 'nonexistent', 'password': 'wrongpassword'})
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == False
        assert '用户名或密码错误' in data['message']
    
    def test_login_existing_username_with_default_password_conflict(self, client):
        """测试6：用户名已存在但密码错误，不能用默认密码自动创建"""
        # Arrange: 先创建一个admin用户（已存在）
        # 然后尝试用默认密码创建同名用户
        response = client.post('/api/login',
            json={'username': 'admin', 'password': '123456'})
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == False
        assert '用户名已存在，密码不正确' in data['message']
    
    def test_login_empty_username(self, client):
        """测试7：用户名为空"""
        # Arrange
        response = client.post('/api/login',
            json={'username': '', 'password': 'password'})
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '用户名和密码不能为空' in data['message']
    
    def test_login_empty_password(self, client):
        """测试8：密码为空"""
        # Arrange
        response = client.post('/api/login',
            json={'username': 'admin', 'password': ''})
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_login_missing_username(self, client):
        """测试9：缺少用户名字段"""
        # Arrange
        response = client.post('/api/login',
            json={'password': 'password'})
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_login_missing_password(self, client):
        """测试10：缺少密码字段"""
        # Arrange
        response = client.post('/api/login',
            json={'username': 'admin'})
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_login_student_role_gets_student_id(self, client):
        """测试11：学生角色用户登录时获取student_id"""
        # Arrange: 创建一个学生用户
        client.post('/api/login',
            json={'username': 'student001', 'password': '123456'})
        
        # Act: 再次登录
        response = client.post('/api/login',
            json={'username': 'student001', 'password': '123456'})
        
        # Assert
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'student_id' in data['user']


class TestStudentManagementModule:
    """测试学生管理模块 - add_student(), get_students() 等方法"""
    
    def test_add_student_successful(self, client):
        """测试12：成功添加学生"""
        # Arrange
        student_data = {
            'student_id': 'STU001',
            'name': '张三',
            'gender': '男',
            'age': 20,
            'phone': '13800138000',
            'email': 'zhangsan@example.com',
            'address': '北京市朝阳区',
            'class_name': '高一1班',
            'teacher_name': '王老师'
        }
        
        # Act
        response = client.post('/api/students', json=student_data)
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert '学生添加成功' in data['message']
    
    def test_add_student_duplicate_student_id(self, client):
        """测试13：学号重复时返回错误"""
        # Arrange: 添加第一个学生
        student_data = {
            'student_id': 'STU002',
            'name': '李四',
            'gender': '女',
            'age': 19,
            'class_name': '高一1班'
        }
        client.post('/api/students', json=student_data)
        
        # Act: 添加同学号的学生
        response = client.post('/api/students', json=student_data)
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '学号已存在' in data['message']
    
    def test_add_student_missing_required_field_student_id(self, client):
        """测试14：缺少学号字段（必填）"""
        # Arrange
        student_data = {
            'name': '王五',
            'gender': '男',
            'age': 21,
            'class_name': '高一2班'
        }
        
        # Act
        response = client.post('/api/students', json=student_data)
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_add_student_missing_required_field_name(self, client):
        """测试15：缺少姓名字段"""
        # Arrange
        student_data = {
            'student_id': 'STU003',
            'gender': '女',
            'age': 20
        }
        
        # Act
        response = client.post('/api/students', json=student_data)
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_add_student_family_info_json_format(self, client, db):
        """测试16：验证family_info存储为正确的JSON格式"""
        # Arrange
        student_data = {
            'student_id': 'STU004',
            'name': '赵六',
            'gender': '男',
            'age': 22,
            'email': 'zhaoliu@example.com',
            'address': '上海市浦东新区',
            'class_name': '高一3班'
        }
        
        # Act
        client.post('/api/students', json=student_data)
        
        # Assert: 验证数据库中的存储格式
        cursor = db.cursor()
        cursor.execute('SELECT family_info FROM students WHERE student_id = ?', 
                      ('STU004',))
        row = cursor.fetchone()
        assert row is not None
        family_info = json.loads(row[0])
        assert family_info['email'] == 'zhaoliu@example.com'
        assert family_info['address'] == '上海市浦东新区'
    
    def test_get_students_pagination_page_1(self, client):
        """测试17：获取学生列表第1页"""
        # Arrange: 添加多个学生
        for i in range(5):
            client.post('/api/students', json={
                'student_id': f'STU_PAGE_{i}',
                'name': f'学生{i}',
                'gender': '男' if i % 2 == 0 else '女',
                'class_name': '高一1班'
            })
        
        # Act
        response = client.get('/api/students?page=1&limit=3')
        
        # Assert
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['page'] == 1
        assert data['limit'] == 3
        assert len(data['data']) <= 3
        assert 'total' in data
    
    def test_get_students_default_pagination(self, client):
        """测试18：获取学生列表使用默认分页参数"""
        # Arrange
        for i in range(3):
            client.post('/api/students', json={
                'student_id': f'STU_DEF_{i}',
                'name': f'学生{i}',
                'gender': '男',
                'class_name': '高一1班'
            })
        
        # Act
        response = client.get('/api/students')
        
        # Assert
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['page'] == 1
        assert data['limit'] == 10
    
    def test_update_student_successful(self, client):
        """测试19：成功更新学生信息"""
        # Arrange: 先添加一个学生
        client.post('/api/students', json={
            'student_id': 'STU_UPD',
            'name': '孙七',
            'gender': '男',
            'age': 20,
            'class_name': '高一1班'
        })
        
        # Act: 更新学生信息
        response = client.put('/api/students/STU_UPD', json={
            'name': '孙七（已更新）',
            'gender': '男',
            'age': 21,
            'email': 'sunqi@example.com',
            'address': '广州市天河区',
            'class_name': '高一2班',
            'teacher_name': '李老师'
        })
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert '学生信息更新成功' in data['message']
    
    def test_delete_student_successful(self, client):
        """测试20：成功删除学生"""
        # Arrange: 先添加一个学生
        client.post('/api/students', json={
            'student_id': 'STU_DEL',
            'name': '周八',
            'gender': '女',
            'class_name': '高一1班'
        })
        
        # Act: 删除学生
        response = client.delete('/api/students/STU_DEL')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert '学生删除成功' in data['message']
    
    def test_delete_student_not_exist(self, client):
        """测试21：删除不存在的学生"""
        # Act
        response = client.delete('/api/students/NONEXISTENT')
        
        # Assert
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
        assert '学生不存在' in data['message']
    
    def test_add_student_field_mapping_phone_to_contact(self, client, db):
        """测试22：验证phone字段映射到contact"""
        # Arrange
        student_data = {
            'student_id': 'STU_MAP1',
            'name': '吴九',
            'gender': '男',
            'phone': '18900009999',
            'class_name': '高一1班'
        }
        
        # Act
        client.post('/api/students', json=student_data)
        
        # Assert
        cursor = db.cursor()
        cursor.execute('SELECT contact FROM students WHERE student_id = ?', 
                      ('STU_MAP1',))
        row = cursor.fetchone()
        assert row[0] == '18900009999'


class TestStudentCourseModule:
    """测试选课管理模块 - add_student_course(), get_student_courses() 等方法"""
    
    def setup_method(self):
        """测试前的准备：添加学生和课程"""
        self.student_id = 'COURSE_STU_001'
        self.course_id = None
    
    def test_add_student_course_successful(self, client, db):
        """测试23：成功添加选课记录"""
        # Arrange: 先添加学生和课程
        client.post('/api/students', json={
            'student_id': 'COURSE_STU_001',
            'name': '课程学生1',
            'gender': '男',
            'class_name': '高一1班'
        })
        
        # 添加课程
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('MATH101', '高等数学', '数学老师', 4, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('MATH101',))
        course_id = cursor.fetchone()[0]
        
        # Act: 选课
        response = client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_001',
            'course_id': course_id,
            'exam_score': 85,
            'daily_score': 90,
            'semester': '2025-秋'
        })
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert '选课添加成功' in data['message']
    
    def test_add_student_course_final_score_calculation(self, client, db):
        """测试24：验证最终成绩计算公式 (exam*0.7 + daily*0.3)"""
        # Arrange
        client.post('/api/students', json={
            'student_id': 'COURSE_STU_002',
            'name': '课程学生2',
            'gender': '女',
            'class_name': '高一1班'
        })
        
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('ENG101', '英语', '英语老师', 3, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('ENG101',))
        course_id = cursor.fetchone()[0]
        
        # Act
        client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_002',
            'course_id': course_id,
            'exam_score': 80,
            'daily_score': 90
        })
        
        # Assert: 验证数据库中的成绩
        cursor.execute('SELECT final_score FROM student_courses WHERE student_id = ? AND course_id = ?',
                      ('COURSE_STU_002', course_id))
        row = cursor.fetchone()
        expected_final = 80 * 0.7 + 90 * 0.3  # 83.0
        assert abs(row[0] - expected_final) < 0.01
    
    def test_add_student_course_zero_scores(self, client, db):
        """测试25：成绩为0的情况"""
        # Arrange
        client.post('/api/students', json={
            'student_id': 'COURSE_STU_003',
            'name': '课程学生3',
            'gender': '男',
            'class_name': '高一2班'
        })
        
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('PHYS101', '物理', '物理老师', 3, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('PHYS101',))
        course_id = cursor.fetchone()[0]
        
        # Act
        response = client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_003',
            'course_id': course_id,
            'exam_score': 0,
            'daily_score': 0
        })
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_add_student_course_missing_student_id(self, client):
        """测试26：缺少学生ID"""
        # Arrange
        response = client.post('/api/student-courses', json={
            'course_id': 1,
            'exam_score': 85
        })
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '学生ID和课程ID不能为空' in data['message']
    
    def test_add_student_course_missing_course_id(self, client):
        """测试27：缺少课程ID"""
        # Arrange
        response = client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_004',
            'exam_score': 85
        })
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_add_student_course_invalid_course_id_type(self, client):
        """测试28：课程ID类型错误（非整数）"""
        # Arrange
        response = client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_005',
            'course_id': 'invalid',
            'exam_score': 85
        })
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '课程ID格式错误' in data['message']
    
    def test_add_student_course_student_not_exist(self, client):
        """测试29：学生不存在"""
        # Arrange
        response = client.post('/api/student-courses', json={
            'student_id': 'NONEXISTENT_STU',
            'course_id': 1,
            'exam_score': 85
        })
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '学生不存在' in data['message']
    
    def test_add_student_course_course_not_exist(self, client):
        """测试30：课程不存在"""
        # Arrange
        client.post('/api/students', json={
            'student_id': 'COURSE_STU_006',
            'name': '课程学生6',
            'gender': '女',
            'class_name': '高一1班'
        })
        
        response = client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_006',
            'course_id': 9999,
            'exam_score': 85
        })
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '课程不存在' in data['message']
    
    def test_add_student_course_duplicate_selection(self, client, db):
        """测试31：防止重复选课"""
        # Arrange
        client.post('/api/students', json={
            'student_id': 'COURSE_STU_007',
            'name': '课程学生7',
            'gender': '男',
            'class_name': '高一1班'
        })
        
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('CHEM101', '化学', '化学老师', 3, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('CHEM101',))
        course_id = cursor.fetchone()[0]
        
        # 第一次选课
        client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_007',
            'course_id': course_id,
            'exam_score': 85
        })
        
        # 第二次选同一课程
        response = client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_007',
            'course_id': course_id,
            'exam_score': 90
        })
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '该学生已选此课程' in data['message']
    
    def test_get_student_courses_by_student_id(self, client, db):
        """测试32：按学生ID查询选课列表"""
        # Arrange: 创建学生和课程并选课
        client.post('/api/students', json={
            'student_id': 'COURSE_STU_008',
            'name': '课程学生8',
            'gender': '女',
            'class_name': '高一1班'
        })
        
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('BIO101', '生物', '生物老师', 3, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('BIO101',))
        course_id = cursor.fetchone()[0]
        
        client.post('/api/student-courses', json={
            'student_id': 'COURSE_STU_008',
            'course_id': course_id,
            'exam_score': 75,
            'daily_score': 88
        })
        
        # Act
        response = client.get('/api/student-courses?student_id=COURSE_STU_008')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert len(data['data']) >= 1
        assert data['data'][0]['student_id'] == 'COURSE_STU_008'


# 测试运行命令
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
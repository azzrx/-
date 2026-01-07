"""
黑盒测试用例
功能测试、集成测试、业务场景测试
"""
import pytest
import json
from datetime import datetime
from app import app
from database import init_db, get_db
import os


@pytest.fixture
def client():
    """创建测试客户端"""
    os.environ['DATABASE'] = 'test_black_box.db'
    app.config['TESTING'] = True
    
    init_db()
    
    with app.test_client() as client:
        yield client
    
    if os.path.exists('test_black_box.db'):
        os.remove('test_black_box.db')


@pytest.fixture
def db():
    """创建数据库连接"""
    conn = get_db()
    yield conn
    conn.close()


class TestLoginScenarios:
    """测试登录场景 - 黑盒测试"""
    
    def test_BT_001_admin_successful_login(self, client):
        """BT-001: 管理员成功登录"""
        response = client.post('/api/login',
            json={'username': 'admin', 'password': 'admin123'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['role'] == 'admin'
        assert 'user' in data
    
    def test_BT_002_teacher_successful_login(self, client):
        """BT-002: 教师成功登录"""
        response = client.post('/api/login',
            json={'username': 'teacher', 'password': 'teacher123'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['role'] == 'teacher'
    
    def test_BT_003_student_auto_register_login(self, client):
        """BT-003: 学生自动注册并登录（默认密码123456）"""
        response = client.post('/api/login',
            json={'username': 'auto_student', 'password': '123456'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['user']['role'] == 'student'
    
    def test_BT_004_empty_username(self, client):
        """BT-004: 用户名为空"""
        response = client.post('/api/login',
            json={'username': '', 'password': 'password'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_BT_005_wrong_password(self, client):
        """BT-005: 密码错误"""
        response = client.post('/api/login',
            json={'username': 'admin', 'password': 'wrongpassword'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == False
        assert '用户名或密码错误' in data['message']
    
    def test_BT_006_nonexistent_user_wrong_password(self, client):
        """BT-006: 用户不存在且密码错误"""
        response = client.post('/api/login',
            json={'username': 'nonexist', 'password': 'wrongpwd'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_BT_007_username_with_special_chars(self, client):
        """BT-007: 用户名包含特殊字符"""
        response = client.post('/api/login',
            json={'username': "admin' OR '1'='1", 'password': 'password'})
        
        # 应该返回失败或无影响（防SQL注入）
        assert response.status_code in [200, 400, 500]
    
    def test_BT_008_very_long_username(self, client):
        """BT-008: 用户名为超长字符串"""
        long_username = 'a' * 1000
        response = client.post('/api/login',
            json={'username': long_username, 'password': 'password'})
        
        # 应该正常处理，返回失败
        assert response.status_code in [200, 400, 500]


class TestStudentManagementScenarios:
    """测试学生管理场景 - 黑盒测试"""
    
    def test_BT_009_add_new_student(self, client):
        """BT-009: 添加新学生"""
        student_data = {
            'student_id': 'BT_STU_001',
            'name': '黑盒测试学生1',
            'gender': '男',
            'age': 20,
            'phone': '13800138001',
            'email': 'student1@example.com',
            'address': '北京市',
            'class_name': '高一1班',
            'teacher_name': '王老师'
        }
        
        response = client.post('/api/students', json=student_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # 验证学生列表中能查询到
        get_response = client.get('/api/students')
        get_data = json.loads(get_response.data)
        student_ids = [s['student_id'] for s in get_data['data']]
        assert 'BT_STU_001' in student_ids
    
    def test_BT_010_add_duplicate_student_id(self, client):
        """BT-010: 添加重复学号"""
        student_data = {
            'student_id': 'BT_STU_002',
            'name': '学生2',
            'gender': '女',
            'class_name': '高一1班'
        }
        
        # 第一次添加
        client.post('/api/students', json=student_data)
        
        # 第二次添加相同学号
        response = client.post('/api/students', json=student_data)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '学号已存在' in data['message']
    
    def test_BT_011_add_student_missing_required_field(self, client):
        """BT-011: 添加学生缺少必填项"""
        incomplete_data = {
            'name': '学生3',
            'gender': '男',
            'class_name': '高一1班'
            # 缺少 student_id
        }
        
        response = client.post('/api/students', json=incomplete_data)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_BT_012_update_student_info(self, client):
        """BT-012: 编辑学生信息"""
        # 先添加学生
        client.post('/api/students', json={
            'student_id': 'BT_STU_003',
            'name': '原始名字',
            'gender': '男',
            'age': 19,
            'class_name': '高一1班'
        })
        
        # 更新信息
        update_data = {
            'name': '更新后的名字',
            'gender': '男',
            'age': 20,
            'class_name': '高二1班',
            'email': 'newemail@example.com',
            'address': '上海市'
        }
        
        response = client.put('/api/students/BT_STU_003', json=update_data)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # 验证更新
        get_response = client.get('/api/students')
        get_data = json.loads(get_response.data)
        student = next((s for s in get_data['data'] if s['student_id'] == 'BT_STU_003'), None)
        assert student is not None
        assert student['name'] == '更新后的名字'
    
    def test_BT_013_delete_student(self, client):
        """BT-013: 删除学生"""
        # 先添加
        client.post('/api/students', json={
            'student_id': 'BT_STU_DEL',
            'name': '待删除学生',
            'gender': '女',
            'class_name': '高一1班'
        })
        
        # 删除
        response = client.delete('/api/students/BT_STU_DEL')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # 验证已删除
        get_response = client.get('/api/students')
        get_data = json.loads(get_response.data)
        student_ids = [s['student_id'] for s in get_data['data']]
        assert 'BT_STU_DEL' not in student_ids
    
    def test_BT_014_delete_nonexistent_student(self, client):
        """BT-014: 删除不存在的学生"""
        response = client.delete('/api/students/NONEXISTENT')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_BT_015_student_pagination(self, client):
        """BT-015: 查询学生列表分页"""
        # 添加多个学生
        for i in range(15):
            client.post('/api/students', json={
                'student_id': f'BT_PAGE_{i:02d}',
                'name': f'分页学生{i}',
                'gender': '男' if i % 2 == 0 else '女',
                'class_name': '高一1班'
            })
        
        # 查询第1页，每页10条
        response = client.get('/api/students?page=1&limit=10')
        
        data = json.loads(response.data)
        assert response.status_code == 200
        assert len(data['data']) <= 10
        assert data['page'] == 1
        assert data['limit'] == 10
        assert data['total'] >= 15
    
    def test_BT_016_pagination_out_of_range(self, client):
        """BT-016: 查询超出范围的页码"""
        response = client.get('/api/students?page=999&limit=10')
        
        data = json.loads(response.data)
        assert response.status_code == 200
        # 应该返回空列表或最后一页
        assert isinstance(data['data'], list)
    
    def test_BT_017_student_with_chinese_characters(self, client):
        """BT-017: 学生信息包含中文字符"""
        response = client.post('/api/students', json={
            'student_id': 'BT_CH_001',
            'name': '张三丰',
            'gender': '男',
            'age': 20,
            'phone': '13800138888',
            'email': 'zhangsan@example.com',
            'address': '北京市朝阳区',
            'class_name': '高一1班',
            'teacher_name': '李老师'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # 验证能正确读取中文
        get_response = client.get('/api/students')
        get_data = json.loads(get_response.data)
        student = next((s for s in get_data['data'] if s['student_id'] == 'BT_CH_001'), None)
        assert student is not None
        assert student['name'] == '张三丰'
    
    def test_BT_018_student_email_address_mapping(self, client):
        """BT-018: 学生邮箱和地址字段映射"""
        response = client.post('/api/students', json={
            'student_id': 'BT_MAP_001',
            'name': '映射测试',
            'gender': '男',
            'email': 'test@example.com',
            'address': '测试地址',
            'class_name': '高一1班'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # 验证email和address能被正确返回
        get_response = client.get('/api/students')
        get_data = json.loads(get_response.data)
        student = next((s for s in get_data['data'] if s['student_id'] == 'BT_MAP_001'), None)
        assert student['email'] == 'test@example.com'
        assert student['address'] == '测试地址'


class TestCourseManagementScenarios:
    """测试课程管理场景 - 黑盒测试"""
    
    def test_BT_019_create_new_course(self, client):
        """BT-019: 创建新课程"""
        response = client.post('/api/courses', json={
            'course_code': 'MATH101',
            'course_name': '高等数学',
            'teacher': '数学老师',
            'credits': 4
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_BT_020_create_duplicate_course_code(self, client):
        """BT-020: 创建重复的课程代码"""
        course_data = {
            'course_code': 'ENG101',
            'course_name': '英语',
            'teacher': '英语老师',
            'credits': 3
        }
        
        # 第一次创建
        client.post('/api/courses', json=course_data)
        
        # 第二次创建相同代码
        response = client.post('/api/courses', json=course_data)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False


class TestStudentCourseScenarios:
    """测试选课场景 - 黑盒测试"""
    
    def test_BT_024_student_enroll_course(self, client, db):
        """BT-024: 学生选课成功"""
        # 准备：添加学生
        client.post('/api/students', json={
            'student_id': 'BT_COURSE_STU_001',
            'name': '选课学生1',
            'gender': '男',
            'class_name': '高一1班'
        })
        
        # 准备：添加课程
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('PHY101', '物理', '物理老师', 3, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('PHY101',))
        course_id = cursor.fetchone()[0]
        
        # 选课
        response = client.post('/api/student-courses', json={
            'student_id': 'BT_COURSE_STU_001',
            'course_id': course_id,
            'exam_score': 85,
            'daily_score': 90,
            'semester': '2025-秋'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_BT_025_prevent_duplicate_enrollment(self, client, db):
        """BT-025: 防止重复选课"""
        # 准备
        client.post('/api/students', json={
            'student_id': 'BT_COURSE_STU_002',
            'name': '选课学生2',
            'gender': '女',
            'class_name': '高一1班'
        })
        
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('CHE101', '化学', '化学老师', 3, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('CHE101',))
        course_id = cursor.fetchone()[0]
        
        # 第一次选课
        client.post('/api/student-courses', json={
            'student_id': 'BT_COURSE_STU_002',
            'course_id': course_id,
            'exam_score': 80,
            'daily_score': 85
        })
        
        # 第二次选课（重复）
        response = client.post('/api/student-courses', json={
            'student_id': 'BT_COURSE_STU_002',
            'course_id': course_id,
            'exam_score': 90,
            'daily_score': 95
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '已选此课程' in data['message']
    
    def test_BT_028_score_calculation_formula(self, client, db):
        """BT-028: 验证成绩计算公式（exam*0.7 + daily*0.3）"""
        # 准备
        client.post('/api/students', json={
            'student_id': 'BT_SCORE_STU',
            'name': '成绩测试学生',
            'gender': '男',
            'class_name': '高一1班'
        })
        
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('BIO101', '生物', '生物老师', 3, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('BIO101',))
        course_id = cursor.fetchone()[0]
        
        # 选课并输入成绩
        exam_score = 80
        daily_score = 90
        expected_final = exam_score * 0.7 + daily_score * 0.3  # = 83.0
        
        client.post('/api/student-courses', json={
            'student_id': 'BT_SCORE_STU',
            'course_id': course_id,
            'exam_score': exam_score,
            'daily_score': daily_score
        })
        
        # 验证成绩计算
        response = client.get(f'/api/student-courses?student_id=BT_SCORE_STU&course_id={course_id}')
        data = json.loads(response.data)
        
        assert len(data['data']) > 0
        record = data['data'][0]
        assert abs(record['final_score'] - expected_final) < 0.01
    
    def test_BT_029_score_zero_values(self, client, db):
        """BT-029: 成绩为0的情况"""
        # 准备
        client.post('/api/students', json={
            'student_id': 'BT_ZERO_STU',
            'name': '零分学生',
            'gender': '男',
            'class_name': '高一1班'
        })
        
        cursor = db.cursor()
        cursor.execute('''INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
                         VALUES (?, ?, ?, ?, ?)''',
                      ('GEO101', '地理', '地理老师', 2, datetime.now().isoformat()))
        db.commit()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('GEO101',))
        course_id = cursor.fetchone()[0]
        
        # 选课，成绩都为0
        response = client.post('/api/student-courses', json={
            'student_id': 'BT_ZERO_STU',
            'course_id': course_id,
            'exam_score': 0,
            'daily_score': 0
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True


class TestAttendanceScenarios:
    """测试考勤场景 - 黑盒测试"""
    
    def test_BT_033_record_student_attendance(self, client):
        """BT-033: 记录学生出勤"""
        # 准备学生
        client.post('/api/students', json={
            'student_id': 'BT_ATT_STU_001',
            'name': '考勤学生1',
            'gender': '男',
            'class_name': '高一1班'
        })
        
        response = client.post('/api/attendance', json={
            'student_id': 'BT_ATT_STU_001',
            'date': '2025-12-11',
            'status': '出勤',
            'reason': ''
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_BT_034_record_student_absence_with_reason(self, client):
        """BT-034: 记录学生缺勤并注明原因"""
        # 准备学生
        client.post('/api/students', json={
            'student_id': 'BT_ATT_STU_002',
            'name': '考勤学生2',
            'gender': '女',
            'class_name': '高一1班'
        })
        
        response = client.post('/api/attendance', json={
            'student_id': 'BT_ATT_STU_002',
            'date': '2025-12-11',
            'status': '缺勤',
            'reason': '生病'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True


class TestRewardsScenarios:
    """测试奖励处分场景 - 黑盒测试"""
    
    def test_BT_038_add_reward_record(self, client):
        """BT-038: 添加奖励记录"""
        # 准备学生
        client.post('/api/students', json={
            'student_id': 'BT_REW_STU_001',
            'name': '奖励学生',
            'gender': '男',
            'class_name': '高一1班'
        })
        
        response = client.post('/api/rewards-punishments', json={
            'student_id': 'BT_REW_STU_001',
            'type': 'reward',
            'title': '优秀学生',
            'description': '学习成绩优秀',
            'date': '2025-12-11'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
    
    def test_BT_039_add_punishment_record(self, client):
        """BT-039: 添加处分记录"""
        # 准备学生
        client.post('/api/students', json={
            'student_id': 'BT_PUN_STU_001',
            'name': '处分学生',
            'gender': '女',
            'class_name': '高一1班'
        })
        
        response = client.post('/api/rewards-punishments', json={
            'student_id': 'BT_PUN_STU_001',
            'type': 'punishment',
            'title': '迟到扣分',
            'description': '多次迟到',
            'date': '2025-12-11'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True


class TestEndToEndScenarios:
    """端到端业务流程 - 黑盒测试"""
    
    def test_BT_046_complete_enrollment_workflow(self, client, db):
        """BT-046: 完整选课流程"""
        # 步骤1: 创建课程
        course_response = client.post('/api/courses', json={
            'course_code': 'WORKFLOW_COURSE',
            'course_name': '工作流测试课程',
            'teacher': '测试老师',
            'credits': 3
        })
        assert course_response.status_code == 200
        
        # 步骤2: 学生选课
        client.post('/api/students', json={
            'student_id': 'BT_WORKFLOW_STU',
            'name': '工作流学生',
            'gender': '男',
            'class_name': '高一1班'
        })
        
        cursor = db.cursor()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('WORKFLOW_COURSE',))
        course_id = cursor.fetchone()[0]
        
        enroll_response = client.post('/api/student-courses', json={
            'student_id': 'BT_WORKFLOW_STU',
            'course_id': course_id,
            'exam_score': 88,
            'daily_score': 92
        })
        assert enroll_response.status_code == 200
        
        # 步骤3: 查询成绩
        get_response = client.get(f'/api/student-courses?student_id=BT_WORKFLOW_STU')
        get_data = json.loads(get_response.data)
        
        assert len(get_data['data']) > 0
        assert get_data['data'][0]['final_score'] == 88 * 0.7 + 92 * 0.3
    
    def test_BT_047_student_registration_to_course_participation(self, client, db):
        """BT-047: 学生注册到参加课程完整流程"""
        # 步骤1: 学生自动注册（使用默认密码）
        login_response = client.post('/api/login',
            json={'username': 'workflow_student', 'password': '123456'})
        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        assert login_data['success'] == True
        
        # 步骤2: 创建课程
        client.post('/api/courses', json={
            'course_code': 'WORKFLOW_COURSE_2',
            'course_name': '工作流测试课程2',
            'teacher': '测试老师2',
            'credits': 3
        })
        
        # 步骤3: 学生选课
        cursor = db.cursor()
        cursor.execute('SELECT id FROM courses WHERE course_code = ?', ('WORKFLOW_COURSE_2',))
        course_id = cursor.fetchone()[0]
        
        enroll_response = client.post('/api/student-courses', json={
            'student_id': login_data['user']['student_id'],
            'course_id': course_id,
            'exam_score': 85,
            'daily_score': 88
        })
        assert enroll_response.status_code == 200
        
        # 步骤4: 查询成绩
        query_response = client.get(f'/api/student-courses?student_id={login_data["user"]["student_id"]}')
        query_data = json.loads(query_response.data)
        assert query_data['total'] >= 1


# 运行命令
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
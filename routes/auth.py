"""用户认证路由"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import hashlib
import random
from database import get_db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                   (username, password_hash))
    user = cursor.fetchone()
    
    # 如果用户不存在，且密码是默认密码123456，则自动创建学生用户和学生记录
    if not user:
        default_password_hash = hashlib.md5('123456'.encode()).hexdigest()
        if password_hash == default_password_hash:
            # 检查用户名是否已存在于users表中（但密码不同）
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                conn.close()
                return jsonify({'success': False, 'message': '用户名已存在，密码不正确'})
            
            try:
                # 创建新用户（角色为学生）
                cursor.execute('INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)',
                             (username, default_password_hash, 'student', datetime.now().isoformat()))
                
                # 检查学生记录是否已存在（通过用户名作为name或student_id）
                cursor.execute('SELECT student_id FROM students WHERE student_id = ? OR name = ? LIMIT 1', 
                             (username, username))
                student = cursor.fetchone()
                
                # 如果学生记录不存在，创建新的学生记录
                if not student:
                    # 使用用户名作为student_id（如果用户名已作为student_id存在，则使用时间戳+用户名）
                    student_id = username
                    # 检查student_id是否唯一
                    cursor.execute('SELECT student_id FROM students WHERE student_id = ?', (student_id,))
                    if cursor.fetchone():
                        # 如果student_id已存在，则生成一个新的唯一student_id
                        student_id = f"{username}_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
                    
                    # 创建学生记录，用户名作为姓名
                    cursor.execute('''
                        INSERT INTO students (student_id, name, gender, age, contact, family_info, class_name, teacher, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (student_id, username, '未知', None, '', '{}', '', '', datetime.now().isoformat()))
                
                conn.commit()
                
                # 重新查询创建的用户
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()
                
                # 获取student_id
                cursor.execute('SELECT student_id FROM students WHERE student_id = ? OR name = ? LIMIT 1', 
                             (username, username))
                student = cursor.fetchone()
                conn.close()
                
                if user:
                    user_data = {
                        'id': user['id'],
                        'username': user['username'],
                        'role': user['role']
                    }
                    if student:
                        user_data['student_id'] = student['student_id']
                    
                    return jsonify({
                        'success': True,
                        'user': user_data,
                        'message': '用户已自动创建'
                    })
            except Exception as e:
                conn.rollback()
                conn.close()
                print(f"Error auto-creating user: {e}")
                return jsonify({'success': False, 'message': f'自动创建用户失败: {str(e)}'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': '用户名或密码错误'})
    
    # 用户已存在，正常登录流程
    if user:
        user_data = {
            'id': user['id'],
            'username': user['username'],
            'role': user['role']
        }
        # 如果是学生角色，尝试获取对应的student_id（假设用户名就是学号或通过用户名查找）
        if user['role'] == 'student':
            # 先尝试用户名就是学号的情况
            cursor.execute('SELECT student_id FROM students WHERE student_id = ?', (user['username'],))
            student = cursor.fetchone()
            # 如果找不到，尝试通过名称匹配（可选）
            if not student:
                cursor.execute('SELECT student_id FROM students WHERE name = ? LIMIT 1', (user['username'],))
                student = cursor.fetchone()
            if student:
                user_data['student_id'] = student['student_id']
        
        conn.close()
        return jsonify({
            'success': True,
            'user': user_data
        })
    else:
        conn.close()
        return jsonify({'success': False, 'message': '用户名或密码错误'})


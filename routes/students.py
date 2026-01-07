"""学生管理路由"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
import json
from database import get_db, execute_with_retry

students_bp = Blueprint('students', __name__)


@students_bp.route('/api/students', methods=['GET'])
def get_students():
    """获取所有学生"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) as total FROM students')
    total = cursor.fetchone()['total']
    
    # Paginate
    cursor.execute('SELECT * FROM students ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, (page - 1) * limit))
    students = []
    for row in cursor.fetchall():
        student = dict(row)
        # 映射字段名以匹配前端
        student['phone'] = student.get('contact', '')
        student['teacher_name'] = student.get('teacher', '')
        
        # 从 family_info 中解析 email 和 address
        family_info = student.get('family_info', '')
        if family_info:
            try:
                # 尝试解析 JSON 格式的 family_info
                family_data = json.loads(family_info)
                student['email'] = family_data.get('email', '')
                student['address'] = family_data.get('address', '')
            except (json.JSONDecodeError, TypeError):
                # 如果不是 JSON 格式，尝试旧格式（用 | 分隔）
                if '|' in family_info:
                    parts = family_info.split('|', 1)
                    student['email'] = parts[0] if len(parts) > 0 else ''
                    student['address'] = parts[1] if len(parts) > 1 else ''
                else:
                    # 旧数据可能是纯文本，作为 email 或 address
                    student['email'] = family_info if '@' in family_info else ''
                    student['address'] = family_info if '@' not in family_info else ''
        else:
            student['email'] = ''
            student['address'] = ''
        
        students.append(student)
    conn.close()
    return jsonify({'total': total, 'data': students, 'page': page, 'limit': limit})


@students_bp.route('/api/students', methods=['POST'])
def add_student():
    """添加学生"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 映射前端字段到数据库字段
        contact = data.get('phone') or data.get('contact', '')
        teacher = data.get('teacher_name') or data.get('teacher', '')
        
        # 将 email 和 address 以 JSON 格式存储在 family_info 中
        email = data.get('email', '')
        address = data.get('address', '')
        family_info_json = json.dumps({'email': email, 'address': address}, ensure_ascii=False)
        
        execute_with_retry(cursor, '''
            INSERT INTO students (student_id, name, gender, age, contact, family_info, class_name, teacher, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['student_id'], data['name'], data['gender'], data.get('age'), contact, family_info_json, data.get('class_name'), teacher, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '学生添加成功'})
    except sqlite3.IntegrityError as e:
        conn.close()
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'success': False, 'message': '学号已存在'}), 400
        elif 'NOT NULL constraint failed' in str(e):
            return jsonify({'success': False, 'message': '必填字段不能为空'}), 400
        else:
            return jsonify({'success': False, 'message': '数据库错误: ' + str(e)}), 500
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'意外错误: {str(e)}'}), 500


@students_bp.route('/api/students/<string:student_id>', methods=['PUT'])
def update_student(student_id):
    """更新学生信息"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    # 映射前端字段到数据库字段
    contact = data.get('phone') or data.get('contact', '')
    teacher = data.get('teacher_name') or data.get('teacher', '')
    
    # 将 email 和 address 以 JSON 格式存储在 family_info 中
    email = data.get('email', '')
    address = data.get('address', '')
    family_info_json = json.dumps({'email': email, 'address': address}, ensure_ascii=False)
    
    try:
        execute_with_retry(cursor, '''
            UPDATE students SET name=?, gender=?, age=?, contact=?, family_info=?,
                          class_name=?, teacher=?
            WHERE student_id=?
        ''', (data['name'], data['gender'], data.get('age'), contact, family_info_json,
              data.get('class_name'), teacher, student_id))
    
        conn.commit()
        print(f"Student {student_id} updated successfully")  # Confirmation log
        conn.close()
        return jsonify({'success': True, 'message': '学生信息更新成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@students_bp.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """删除学生"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, 'DELETE FROM students WHERE student_id=?', (student_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '学生不存在'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': '学生删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


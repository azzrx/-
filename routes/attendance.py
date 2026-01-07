"""考勤管理路由"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from database import get_db, execute_with_retry

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/api/attendance', methods=['GET'])
def get_attendance():
    student_id = request.args.get('student_id')
    course_id = request.args.get('course_id')
    date = request.args.get('date')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT a.*, s.name as student_name, s.class_name, c.course_name
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        LEFT JOIN courses c ON a.course_id = c.id
        WHERE 1=1
    '''
    params = []
    
    if student_id:
        query += ' AND a.student_id = ?'
        params.append(student_id)
    if course_id:
        query += ' AND a.course_id = ?'
        params.append(course_id)
    if date:
        query += ' AND a.date = ?'
        params.append(date)
    
    # Get total count
    count_query = f'SELECT COUNT(*) as total FROM ({query})'
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Paginate
    query += ' ORDER BY a.date DESC LIMIT ? OFFSET ?'
    params.extend([limit, (page - 1) * limit])
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'total': total, 'data': results, 'page': page, 'limit': limit})


@attendance_bp.route('/api/attendance', methods=['POST'])
def add_attendance():
    """添加考勤记录"""
    data = request.json
    print(f"Received attendance data: {data}")  # Debug print
    
    if not data or not data.get('student_id') or not data.get('date') or not data.get('status'):
        return jsonify({'success': False, 'message': '学生ID、日期和状态不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, '''
            INSERT INTO attendance (student_id, course_id, date, status, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['student_id'], data.get('course_id'), data['date'], data['status'], 
              data.get('reason', ''), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '考勤记录添加成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@attendance_bp.route('/api/attendance/<int:id>', methods=['PUT'])
def update_attendance(id):
    """更新考勤记录"""
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
    
    if not data.get('status'):
        return jsonify({'success': False, 'message': '状态不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 检查考勤记录是否存在
        cursor.execute('SELECT * FROM attendance WHERE id=?', (id,))
        existing_record = cursor.fetchone()
        if not existing_record:
            conn.close()
            return jsonify({'success': False, 'message': '考勤记录不存在'}), 404
        
        # 验证学生是否存在（如果提供了student_id）
        student_id = data.get('student_id')
        if student_id is not None:
            cursor.execute('SELECT student_id FROM students WHERE student_id=?', (student_id,))
            student = cursor.fetchone()
            if not student:
                conn.close()
                return jsonify({'success': False, 'message': '学生不存在'}), 400
        
        # 验证课程是否存在（如果提供了course_id且不为空）
        course_id = data.get('course_id')
        if course_id is not None and course_id != '' and course_id != 0:
            try:
                course_id = int(course_id)
                cursor.execute('SELECT id FROM courses WHERE id=?', (course_id,))
                course = cursor.fetchone()
                if not course:
                    conn.close()
                    return jsonify({'success': False, 'message': '课程不存在'}), 400
            except (ValueError, TypeError):
                conn.close()
                return jsonify({'success': False, 'message': '课程ID格式错误'}), 400
        elif course_id == '' or course_id == 0:
            course_id = None
        
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if student_id is not None:
            update_fields.append('student_id=?')
            update_values.append(student_id)
        
        if course_id is not None:
            update_fields.append('course_id=?')
            update_values.append(course_id)
        elif course_id == '' or (course_id is not None and course_id == 0):
            update_fields.append('course_id=?')
            update_values.append(None)
        
        if data.get('date'):
            update_fields.append('date=?')
            update_values.append(data['date'])
        
        update_fields.append('status=?')
        update_values.append(data['status'])
        
        update_fields.append('reason=?')
        update_values.append(data.get('reason') or '')
        
        update_values.append(id)
        
        update_query = f'UPDATE attendance SET {", ".join(update_fields)} WHERE id=?'
        execute_with_retry(cursor, update_query, tuple(update_values))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '考勤记录更新失败'}), 500
        
        conn.close()
        return jsonify({'success': True, 'message': '考勤记录更新成功'})
    except Exception as e:
        conn.close()
        print(f"Update attendance error: {e}")  # Debug print
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@attendance_bp.route('/api/attendance/<int:id>', methods=['DELETE'])
def delete_attendance(id):
    """删除考勤记录"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, 'DELETE FROM attendance WHERE id=?', (id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '考勤记录不存在'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': '考勤记录删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


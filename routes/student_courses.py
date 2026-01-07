"""学生选课和成绩管理路由"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
from database import get_db, execute_with_retry

student_courses_bp = Blueprint('student_courses', __name__)


@student_courses_bp.route('/api/student-courses', methods=['GET'])
def get_student_courses():
    """获取学生选课信息"""
    student_id = request.args.get('student_id')
    course_id = request.args.get('course_id')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT sc.*, c.course_code, c.course_name, c.teacher, c.credits,
               s.name as student_name
        FROM student_courses sc
        LEFT JOIN courses c ON sc.course_id = c.id
        LEFT JOIN students s ON sc.student_id = s.student_id
        WHERE 1=1
    '''
    params = []
    
    if student_id:
        query += ' AND sc.student_id = ?'
        params.append(student_id)
    if course_id:
        query += ' AND sc.course_id = ?'
        params.append(course_id)
    
    # Get total count
    count_query = f'SELECT COUNT(*) as total FROM ({query})'
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Paginate
    query += ' ORDER BY sc.created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, (page - 1) * limit])
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    print(f"Found {len(results)} student course records")  # Debug log
    conn.close()
    return jsonify({'total': total, 'data': results, 'page': page, 'limit': limit})


@student_courses_bp.route('/api/student-courses', methods=['POST'])
def add_student_course():
    """学生选课"""
    data = request.json
    print(f"Received student course data: {data}")
    
    if not data or not data.get('student_id') or not data.get('course_id'):
        return jsonify({'success': False, 'message': '学生ID和课程ID不能为空'}), 400
    
    # 确保 course_id 是整数
    try:
        course_id = int(data['course_id'])
        student_id = str(data['student_id']).strip()
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '课程ID格式错误'}), 400
    
    if not student_id:
        return jsonify({'success': False, 'message': '学生ID不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查学生和课程是否存在
    cursor.execute('SELECT student_id FROM students WHERE student_id = ?', (student_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '学生不存在'}), 400
    
    cursor.execute('SELECT id FROM courses WHERE id = ?', (course_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '课程不存在'}), 400
    
    # 检查是否已选课
    cursor.execute('SELECT id FROM student_courses WHERE student_id = ? AND course_id = ?', 
                   (student_id, course_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '该学生已选此课程'}), 400
    
    try:
        # 计算总成绩
        exam_score = float(data.get('exam_score', 0)) if data.get('exam_score') else 0
        daily_score = float(data.get('daily_score', 0)) if data.get('daily_score') else 0
        final_score = exam_score * 0.7 + daily_score * 0.3
        
        execute_with_retry(cursor, '''
            INSERT INTO student_courses (student_id, course_id, exam_score, 
                                        daily_score, final_score, semester, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, course_id, exam_score, daily_score,
              final_score, data.get('semester'), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '选课添加成功'})
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'success': False, 'message': f'选课记录已存在或数据错误: {str(e)}'}), 400
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@student_courses_bp.route('/api/student-courses/<int:id>', methods=['PUT'])
def update_student_course(id):
    """更新学生选课记录（包括课程、成绩和学期）"""
    data = request.json
    print(f"Received data for update: {data}")  # Debug print
    
    if not data:
        return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # 检查选课记录是否存在
        cursor.execute('SELECT * FROM student_courses WHERE id=?', (id,))
        existing_record = cursor.fetchone()
        if not existing_record:
            conn.close()
            return jsonify({'success': False, 'message': '选课记录不存在'}), 404
        
        # 获取更新数据
        exam_score = data.get('exam_score', 0) or 0
        daily_score = data.get('daily_score', 0) or 0
        final_score = exam_score * 0.7 + daily_score * 0.3
        semester = data.get('semester')
        
        # 如果提供了course_id，验证课程是否存在并检查重复
        course_id = data.get('course_id')
        if course_id is not None:
            try:
                course_id = int(course_id)
                cursor.execute('SELECT id FROM courses WHERE id=?', (course_id,))
                course = cursor.fetchone()
                if not course:
                    conn.close()
                    return jsonify({'success': False, 'message': '课程不存在'}), 400
                
                # 如果课程改变，检查是否会产生重复记录
                if course_id != existing_record['course_id']:
                    student_id = data.get('student_id') or existing_record['student_id']
                    cursor.execute('SELECT id FROM student_courses WHERE student_id=? AND course_id=? AND id!=?', 
                                 (student_id, course_id, id))
                    duplicate = cursor.fetchone()
                    if duplicate:
                        conn.close()
                        return jsonify({'success': False, 'message': '该学生已选择此课程'}), 400
            except (ValueError, TypeError):
                conn.close()
                return jsonify({'success': False, 'message': '课程ID格式错误'}), 400
        
        # 如果提供了student_id，验证学生是否存在
        student_id = data.get('student_id')
        if student_id is not None:
            cursor.execute('SELECT student_id FROM students WHERE student_id=?', (student_id,))
            student = cursor.fetchone()
            if not student:
                conn.close()
                return jsonify({'success': False, 'message': '学生不存在'}), 400
        
        # 构建更新语句，只更新提供的字段
        update_fields = []
        update_values = []
        
        if course_id is not None:
            update_fields.append('course_id=?')
            update_values.append(course_id)
        
        if student_id is not None:
            update_fields.append('student_id=?')
            update_values.append(student_id)
        
        update_fields.append('exam_score=?')
        update_values.append(exam_score)
        
        update_fields.append('daily_score=?')
        update_values.append(daily_score)
        
        update_fields.append('final_score=?')
        update_values.append(final_score)
        
        if semester is not None:
            update_fields.append('semester=?')
            update_values.append(semester)
        
        update_values.append(id)
        
        update_query = f'UPDATE student_courses SET {", ".join(update_fields)} WHERE id=?'
        execute_with_retry(cursor, update_query, tuple(update_values))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '选课记录更新失败'}), 500
        
        conn.close()
        return jsonify({'success': True, 'message': '更新成功'})
    except Exception as e:
        conn.close()
        print(f"Update error: {e}")  # Debug print
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@student_courses_bp.route('/api/student-courses/<int:id>', methods=['DELETE'])
def delete_student_course(id):
    """删除学生选课记录"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, 'DELETE FROM student_courses WHERE id=?', (id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '选课记录不存在'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': '选课记录删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


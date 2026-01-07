"""课程管理路由"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
from database import get_db, execute_with_retry

courses_bp = Blueprint('courses', __name__)


@courses_bp.route('/api/courses', methods=['GET'])
def get_courses():
    """获取所有课程"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) as total FROM courses')
    total = cursor.fetchone()['total']
    
    # Paginate
    cursor.execute('SELECT * FROM courses ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, (page - 1) * limit))
    courses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'total': total, 'data': courses, 'page': page, 'limit': limit})


@courses_bp.route('/api/courses', methods=['POST'])
def add_course():
    """添加课程"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, '''
            INSERT INTO courses (course_code, course_name, teacher, credits, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (data.get('course_code'), data['course_name'], data.get('teacher'),
              data.get('credits'), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '课程添加成功'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': '课程代码已存在'}), 400
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@courses_bp.route('/api/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    """更新课程"""
    data = request.json
    
    if not data or not data.get('course_name'):
        return jsonify({'success': False, 'message': '课程名称不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, '''
            UPDATE courses SET course_name=?, teacher=?, credits=?
            WHERE id=?
        ''', (data['course_name'], data.get('teacher'), data.get('credits'), course_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '课程更新成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@courses_bp.route('/api/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    """删除课程"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, 'DELETE FROM courses WHERE id=?', (course_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '课程不存在'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': '课程删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


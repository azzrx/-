"""统计分析路由"""
from flask import Blueprint, jsonify
from database import get_db

statistics_bp = Blueprint('statistics', __name__)


@statistics_bp.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计数据"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 学生总数
    cursor.execute('SELECT COUNT(*) as count FROM students')
    student_count = cursor.fetchone()['count']
    
    # 课程总数
    cursor.execute('SELECT COUNT(*) as count FROM courses')
    course_count = cursor.fetchone()['count']
    
    # 平均成绩
    cursor.execute('SELECT AVG(final_score) as avg_score FROM student_courses')
    avg_score = cursor.fetchone()['avg_score'] or 0
    
    # 出勤率
    cursor.execute('SELECT COUNT(*) as total FROM attendance')
    total_attendance = cursor.fetchone()['total']
    cursor.execute("SELECT COUNT(*) as present FROM attendance WHERE status='出勤'")
    present_count = cursor.fetchone()['present']
    attendance_rate = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    
    # 按课程分组的出勤率和平均成绩
    course_statistics = []
    cursor.execute('SELECT id, course_code, course_name FROM courses')
    courses = cursor.fetchall()
    
    for course in courses:
        course_id = course['id']
        course_code = course['course_code'] or ''
        course_name = course['course_name']
        
        # 该课程的平均成绩
        cursor.execute('''
            SELECT AVG(final_score) as avg_score 
            FROM student_courses 
            WHERE course_id = ?
        ''', (course_id,))
        course_avg_score = cursor.fetchone()['avg_score']
        course_avg_score = round(course_avg_score, 2) if course_avg_score else 0
        
        # 该课程的出勤率
        cursor.execute('SELECT COUNT(*) as total FROM attendance WHERE course_id = ?', (course_id,))
        course_total_attendance = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as present FROM attendance WHERE course_id = ? AND status='出勤'", (course_id,))
        course_present_count = cursor.fetchone()['present']
        course_attendance_rate = (course_present_count / course_total_attendance * 100) if course_total_attendance > 0 else 0
        
        course_statistics.append({
            'course_id': course_id,
            'course_code': course_code,
            'course_name': course_name,
            'avg_score': round(course_avg_score, 2),
            'attendance_rate': round(course_attendance_rate, 2)
        })
    
    conn.close()
    
    return jsonify({
        'student_count': student_count,
        'course_count': course_count,
        'avg_score': round(avg_score, 2),
        'attendance_rate': round(attendance_rate, 2),
        'course_statistics': course_statistics
    })


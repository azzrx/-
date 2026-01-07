from typing import List, Dict, Optional
from database import get_db, execute_with_retry
from datetime import datetime


class StudentService:
    def __init__(self):
        pass

    def add_student(self, data: Dict) -> bool:
        """示例：将前端数据映射并插入 students 表"""
        conn = get_db()
        cursor = conn.cursor()
        try:
            contact = data.get('phone') or data.get('contact', '')
            teacher = data.get('teacher_name') or data.get('teacher', '')
            email = data.get('email', '')
            address = data.get('address', '')
            family_info_json = __import__('json').dumps({'email': email, 'address': address}, ensure_ascii=False)

            execute_with_retry(cursor, '''
                INSERT INTO students (student_id, name, gender, age, contact, family_info, class_name, teacher, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['student_id'], data['name'], data['gender'], data.get('age'), contact, family_info_json, data.get('class_name'), teacher, datetime.now().isoformat()))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_all_students(self, page: int = 1, limit: int = 10) -> Dict:
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT COUNT(*) as total FROM students')
            total = cursor.fetchone()['total']
            cursor.execute('SELECT * FROM students ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, (page - 1) * limit))
            students = [dict(row) for row in cursor.fetchall()]
            return {'total': total, 'data': students, 'page': page, 'limit': limit}
        finally:
            conn.close()

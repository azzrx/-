"""家长管理路由"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from database import get_db, execute_with_retry

parents_bp = Blueprint('parents', __name__)


@parents_bp.route('/api/parents', methods=['GET'])
def get_parents():
    """获取家长信息"""
    student_id = request.args.get('student_id')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT p.*, s.name as student_name, s.student_id
        FROM parents p
        JOIN students s ON p.student_id = s.student_id
        WHERE 1=1
    '''
    params = []
    
    if student_id:
        query += ' AND p.student_id = ?'
        params.append(student_id)
    
    # Get total count
    count_query = f'SELECT COUNT(*) as total FROM ({query})'
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Paginate
    query += ' ORDER BY p.created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, (page - 1) * limit])
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'total': total, 'data': results, 'page': page, 'limit': limit})


@parents_bp.route('/api/parents', methods=['POST'])
def add_parent():
    """添加家长信息"""
    data = request.json
    
    if not data or not data.get('student_id') or not data.get('parent_name') or not data.get('relationship') or not data.get('phone'):
        return jsonify({'success': False, 'message': '学生ID、家长姓名、关系和电话不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, '''
            INSERT INTO parents (student_id, parent_name, relationship, phone, email, address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['student_id'], data['parent_name'], data['relationship'],
              data['phone'], data.get('email'), data.get('address'),
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '家长信息添加成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@parents_bp.route('/api/parents/<int:id>', methods=['PUT'])
def update_parent(id):
    """更新家长信息"""
    data = request.json
    
    if not data or not data.get('parent_name') or not data.get('relationship') or not data.get('phone'):
        return jsonify({'success': False, 'message': '家长姓名、关系和电话不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, '''
            UPDATE parents SET parent_name=?, relationship=?, phone=?, email=?, address=?
            WHERE id=?
        ''', (data['parent_name'], data['relationship'], data['phone'],
              data.get('email'), data.get('address'), id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '家长信息更新成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@parents_bp.route('/api/parents/<int:id>', methods=['DELETE'])
def delete_parent(id):
    """删除家长信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, 'DELETE FROM parents WHERE id=?', (id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '家长信息不存在'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': '家长信息删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


"""奖励处分管理路由"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from database import get_db, execute_with_retry

rewards_bp = Blueprint('rewards', __name__)


@rewards_bp.route('/api/rewards-punishments', methods=['GET'])
def get_rewards_punishments():
    """获取奖励处分记录"""
    student_id = request.args.get('student_id')
    rp_type = request.args.get('type')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = '''
        SELECT rp.*, s.name as student_name
        FROM rewards_punishments rp
        JOIN students s ON rp.student_id = s.student_id
        WHERE 1=1
    '''
    params = []
    
    if student_id:
        query += ' AND rp.student_id = ?'
        params.append(student_id)
    if rp_type:
        query += ' AND rp.type = ?'
        params.append(rp_type)
    
    # Get total count
    count_query = f'SELECT COUNT(*) as total FROM ({query})'
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Paginate
    query += ' ORDER BY rp.date DESC LIMIT ? OFFSET ?'
    params.extend([limit, (page - 1) * limit])
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'total': total, 'data': results, 'page': page, 'limit': limit})


@rewards_bp.route('/api/rewards-punishments', methods=['POST'])
def add_reward_punishment():
    """添加奖励处分记录"""
    data = request.json
    
    if not data or not data.get('student_id') or not data.get('type') or not data.get('title') or not data.get('date'):
        return jsonify({'success': False, 'message': '学生ID、类型、标题和日期不能为空'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, '''
            INSERT INTO rewards_punishments (student_id, type, title, description, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['student_id'], data['type'], data['title'], 
              data.get('description'), data['date'], datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '记录添加成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@rewards_bp.route('/api/rewards-punishments/<int:id>', methods=['DELETE'])
def delete_reward_punishment(id):
    """删除奖励处分记录"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, 'DELETE FROM rewards_punishments WHERE id=?', (id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': '记录删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


"""用户管理路由"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
import hashlib
from database import get_db, execute_with_retry

users_bp = Blueprint('users', __name__)


@users_bp.route('/api/users', methods=['GET'])
def get_users():
    """获取所有用户"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    
    conn = get_db()
    db_cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) as total FROM users')
    total = cursor.fetchone()['total']
    
    # Paginate
    cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, (page - 1) * limit))
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'total': total, 'data': users, 'page': page, 'limit': limit})


@users_bp.route('/api/users', methods=['POST'])
def add_user():
    """添加用户"""
    data = request.json
    conn = get_db()
    db_cursor = conn.cursor()
    
    if not data.get('password'):
        conn.close()
        return jsonify({'success': False, 'message': '密码不能为空'}), 400
    
    password_hash = hashlib.md5(data['password'].encode()).hexdigest()
    
    try:
        execute_with_retry(cursor, '''
            INSERT INTO users (username, password, role, created_at)
            VALUES (?, ?, ?, ?)
        ''', (data['username'], password_hash, data.get('role', 'admin'),
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '用户添加成功'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': '用户名已存在'}), 400
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户"""
    data = request.json
    
    if not data:
        return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
    
    conn = get_db()
    db_cursor = conn.cursor()
    
    try:
        # 先获取当前用户信息
        cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
        current_user = cursor.fetchone()
        
        if not current_user:
            conn.close()
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 如果只提供密码，只更新密码，保留原有角色
        if 'password' in data and data['password'] and 'role' not in data:
            password_hash = hashlib.md5(data['password'].encode()).hexdigest()
            execute_with_retry(cursor, 'UPDATE users SET password=? WHERE id=?',
                          (password_hash, user_id))
        # 如果同时提供密码和角色，更新两者
        elif 'password' in data and data['password'] and 'role' in data:
            password_hash = hashlib.md5(data['password'].encode()).hexdigest()
            execute_with_retry(cursor, 'UPDATE users SET password=?, role=? WHERE id=?',
                          (password_hash, data.get('role'), user_id))
        # 如果只提供角色，只更新角色
        elif 'role' in data:
            execute_with_retry(cursor, 'UPDATE users SET role=? WHERE id=?',
                          (data.get('role'), user_id))
        else:
            conn.close()
            return jsonify({'success': False, 'message': '请提供要更新的字段'}), 400
        
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '用户更新失败'}), 500
        
        conn.close()
        return jsonify({'success': True, 'message': '用户更新成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    conn = get_db()
    db_cursor = conn.cursor()
    
    try:
        execute_with_retry(cursor, 'DELETE FROM users WHERE id=?', (user_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        conn.close()
        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


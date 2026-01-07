"""数据库相关函数"""
import sqlite3
import time
import hashlib
import json
import random
from datetime import datetime
from config import DATABASE


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DATABASE, timeout=30, isolation_level='IMMEDIATE')
    cursor = conn.cursor()
    print("Initializing database...")  # Debug
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            created_at TEXT NOT NULL
        )
    ''')
    print("Users table created/checked")
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER,
            contact TEXT,
            family_info TEXT,
            class_name TEXT,
            teacher TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    print("Students table created/checked")
    
    # 课程表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE,
            course_name TEXT NOT NULL,
            teacher TEXT,
            credits INTEGER,
            created_at TEXT NOT NULL
        )
    ''')
    print("Courses table created/checked")
    
    # 学生选课表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            exam_score REAL,
            daily_score REAL,
            final_score REAL,
            semester TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    ''')
    print("Student_courses table created/checked")
    
    # 考勤表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    ''')
    print("Attendance table created/checked")
    
    # Migration: Add course_id if not exists
    cursor.execute("PRAGMA table_info(attendance)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'course_id' not in columns:
        cursor.execute('ALTER TABLE attendance ADD COLUMN course_id INTEGER')
        print("Added course_id to attendance table")
    
    # 奖励处分表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards_punishments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    print("Rewards_punishments table created/checked")
    
    # 家长表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            parent_name TEXT NOT NULL,
            relationship TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    print("Parents table created/checked")
    
    # Add default users if not exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ('admin', hashlib.md5('admin123'.encode()).hexdigest(), 'admin'),
            ('teacher', hashlib.md5('teacher123'.encode()).hexdigest(), 'teacher'),
            ('student', hashlib.md5('student123'.encode()).hexdigest(), 'student')
        ]
        for username, password, role in default_users:
            cursor.execute('INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)', 
                           (username, password, role, datetime.now().isoformat()))
        print("Default users added")
    
    conn.commit()
    conn.close()
    print("Database initialization complete")


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE, timeout=30, isolation_level='IMMEDIATE')
    conn.row_factory = sqlite3.Row
    return conn


def execute_with_retry(cursor, query, params):
    """带重试机制的数据库执行"""
    retries = 10
    for attempt in range(retries):
        try:
            cursor.execute(query, params)
            return  # Success
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < retries - 1:
                print(f"Database locked, retrying in 2s (attempt {attempt + 1})")
                time.sleep(2)
            else:
                raise


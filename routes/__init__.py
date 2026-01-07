"""路由注册"""
from . import auth, students, courses, student_courses, attendance, rewards, parents, users, statistics

def register_routes(app):
    """注册所有路由到Flask应用"""
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(students.students_bp)
    app.register_blueprint(courses.courses_bp)
    app.register_blueprint(student_courses.student_courses_bp)
    app.register_blueprint(attendance.attendance_bp)
    app.register_blueprint(rewards.rewards_bp)
    app.register_blueprint(parents.parents_bp)
    app.register_blueprint(users.users_bp)
    app.register_blueprint(statistics.statistics_bp)


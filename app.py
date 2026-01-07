"""Flask应用主文件"""
from flask import Flask, render_template
from flask_cors import CORS
from database import init_db
from routes import register_routes

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 注册所有路由
register_routes(app)


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 注册蓝图
from routes.data_management import data_bp
from routes.preprocessing import preprocessing_bp
from routes.detection import detection_bp

app.register_blueprint(data_bp)
app.register_blueprint(preprocessing_bp)
app.register_blueprint(detection_bp)

@app.route('/')
def index():
    return jsonify({
        'message': 'Welcome to Flask Backend API',
        'status': 'running'
    })

@app.route('/api/hello')
def hello():
    return jsonify({
        'message': 'hello'
    })

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'port': 5555
    })

@app.route('/api/data', methods=['GET'])
def get_data():
    # 示例 GET 端点
    return jsonify({
        'data': 'Sample data from backend',
        'timestamp': '2025-10-17'
    })

@app.route('/api/data', methods=['POST'])
def post_data():
    # 示例 POST 端点
    data = request.get_json()
    return jsonify({
        'message': 'Data received successfully',
        'received_data': data
    }), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)

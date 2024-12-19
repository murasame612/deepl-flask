from flask import Blueprint, render_template, request, jsonify, redirect, send_file, url_for, session,current_app
import os
import numpy as np
import cv2
import base64
from process.processImage import detect, generate_html

apr = Blueprint('apr', __name__)
users_db={
    "admin": {"password": "admin"},
}

@apr.before_request
def check_login():
    # 如果用户未登录并且请求的不是登录或注册路由，则重定向到登录页面
    if 'username' not in session and request.endpoint not in ['apr.login', 'apr.logout','apr.register']:
        return redirect(url_for('apr.login'))
    
@apr.route('/')
def index():
    return redirect(url_for('apr.main'))

@apr.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = users_db.get(username)
        if user and user['password'] == password:
            session['username'] = username
            return jsonify({'success': True})
        else:
            return jsonify({'success': False}), 401
    return render_template('login.html')

@apr.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if username in users_db:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400

        # 保存用户数据
        users_db[username] = {'password': password}
        return jsonify({'success': True})

    return render_template('register.html')

@apr.route('/main')
def main():
    user = session.get('username')
    with open ("./user/test.html","r",encoding="utf-8") as f:
        result = f.read()
    return render_template('main.html', user=user)


@apr.route('/logout', methods=['POST'])
def logout():
    # 清除 session 中的用户名
    session.pop('username', None)
    print("已注销")
    return redirect(url_for('apr.login'))

# 检查文件扩展名是否被允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@apr.route('/upload_image', methods=['POST'])
def upload_image():
    """
    处理上传的图像文件，并返回处理后的图像和相关信息。

    该函数执行以下步骤：
    1. 检查请求中是否包含图像文件。
    2. 验证文件名是否为空。
    3. 使用 OpenCV 读取图像文件并进行处理。
    4. 将处理后的图像转换为 base64 编码。
    5. 返回处理后的图像和相关文本信息。
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    file_bytes = np.frombuffer(file.read(), np.uint8)
    # 使用 OpenCV 解码为图像
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    ret_image = detect(image,session.get('username'))
    # 生成展示
    
    #!!项目根目录为开始路径
    user_path = os.path.join("user",session.get('username'),"latest","image")
    #生成答案容器
    result_html = generate_html(user_path,session.get('username'))

    # 保存图片为jpeg
    _, buffer = cv2.imencode('.jpg', ret_image)#image更换为你输入的cv2图片对象
    # 将图片编码为 base64 字符串
    encoded_string = base64.b64encode(buffer).decode('utf-8')

    # 假设返回的一张图片和两个字符串
    #返回base64编码后的图片和文本
    return jsonify({
        'imageUrl': encoded_string,
        "result_html": result_html
    })

@apr.route('/<path:user>/image/<path:filename>')
def serve_image(user, filename):
    """
    静态托管图片
    :param user:
    :param filename:
    :return:
    """
    absolute_path = os.path.join("..",'user', user, 'latest', 'image', filename)
    return send_file(absolute_path)



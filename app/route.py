
from flask import Blueprint, render_template, request, jsonify, redirect, send_file, url_for, session,current_app
import os
import numpy as np
import cv2
import base64
from process.processImage import detect, generate_html
import json
from .account import add_account_to_csv, verify_account,read_accounts_from_csv

#注册蓝图
apr = Blueprint('apr', __name__)
#账号csv的路径
csv_file = 'account.csv'



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
    """
    登陆界面路由函数
    """
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        accounts = read_accounts_from_csv(csv_file)
        if verify_account(accounts, username, password):
            session['username'] = username
            return jsonify({'success': True})
        else:
            return jsonify({'success': False}), 401
    return render_template('login.html')

@apr.route('/register', methods=['GET', 'POST'])
def register():
    """
    注册路由函数
    """
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        accounts = read_accounts_from_csv(csv_file)
        if username in accounts:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400

        # 保存用户数据
        add_account_to_csv(csv_file,username, password)
        return jsonify({'success': True})

    return render_template('register.html')

@apr.route('/main')
def main():
    """
    主页面
    """
    user = session.get('username')
    # 传递用户名到模板
    return render_template('main.html', user=user)

@apr.route("/analysis")
def analysis():
    """
    分析页面
    """
    user = session.get('username')
    # 传递用户名到模板
    return render_template("analysis.html",user=user)

########################################
#下方为函数URL

@apr.route('/logout', methods=['POST'])
def logout():
    # 清除 session 中的用户名,注销
    session.pop('username', None)
    print("已注销")
    return redirect(url_for('apr.login'))


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
    # 切割图片,进行ocr识别,切割
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

    #返回base64编码后的图片和公式批改的html
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

@apr.route('/call_python_function', methods=['POST'])
def call_python_function():
    """
    点击按钮后的处理函数,按钮功能是将记录改成正确的,即将json文件中的correct字段改为True
    :return:
    """
    #按钮返回的json数据
    data = request.get_json()
    #获得图片名
    image_name = data.get('image_name')
    #获得用户名
    user = data.get("user")
    #获得图片的json文件名
    j_name = image_name.replace(".png", ".json")
    #根据user图片的json文件路径,open的路径是项目根目录
    json_file_path = os.path.join("user",user, "latest", "json",j_name)
    #打开json文件
    with open(json_file_path, 'r', encoding='GBK') as f:
        data = json.load(f)
    #将json文件中的correct字段改为True
    data["correct"] = True
    #写回json
    with open(json_file_path, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"{image_name} correct")
    # 可以返回一个响应
    return jsonify({"status": "success", "image_name": image_name,"user":user})

from process.getSum import save_in_user

@apr.route('/submit', methods=['POST'])
def submit():
    """
    提交按钮的处理函数,按钮功能是将用户的答题记录保存到用户的history文件夹下
    """
    save_in_user(session.get('username'))
    return jsonify({'success': True})


from GPT.LLM import chat
@apr.route('/ana_report',methods=['POST'])
def ana_report():
    """
    openai生成html
    """
    user = session.get('username')
    result_html = chat(user)
    return jsonify({"html":result_html})


from process.getSum import gen_ala_html
@apr.route('/ana_sum',methods=['POST'])
def ana_sum_report():
    """
    生成简单总结和饼图
    """
    user = session.get('username')
    result_html = gen_ala_html(user)
    return jsonify({"html":result_html})

@apr.route('/<path:user>/history/<path:filename>')
def serve_pie_image(user, filename):
    """
    静态托管图片
    :param user:
    :param filename:
    :return:
    """
    
    absolute_path = os.path.join("..",'user', user, 'history',filename)
    return send_file(absolute_path)


@apr.route("/about")
def about():
    user = session.get("username")
    if user is None:
        redirect(url_for(apr.login))
    return render_template("about.html",user = user)

from process.model import delete_his_json
@apr.route("/delete_his",methods=["post"])
def delete_his():
    user = session.get("username")
    #删除用户的历史记录
    delete_his_json(user)
    return jsonify({"status":"success"})

#不缓存图片
@apr.after_request
def add_cache_control(response):
    # 设置所有静态文件的缓存控制
    if response.content_type.startswith('image'):
        response.cache_control.no_store = True  # 不缓存图片
        response.cache_control.max_age = 0
    return response

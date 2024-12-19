from PIL import Image
from process.model import get_all_file_paths
from process.nms import draw_nms_boxes, infer_nms_bboxes
import cv2
import numpy as np
from process.pddocr import ocr_and_save, process_wrong_image
from process.model import clear_folder

"""
该文件主要处理的是主页面传入的图片，并进行分割处理，然后生成HTML文件。到flask返回HTML文件
"""
def _crop_image(img, x, y, w, h):
    # 计算裁剪区域的左上角和右下角
    top_left_x = int(x - w / 2)
    top_left_y = int(y - h / 2)
    bottom_right_x = int(x + w / 2)
    bottom_right_y = int(y + h / 2)

    # 防止越界
    top_left_x = max(top_left_x, 0)
    top_left_y = max(top_left_y, 0)
    bottom_right_x = min(bottom_right_x, img.shape[1])
    bottom_right_y = min(bottom_right_y, img.shape[0])

    # 裁剪图像
    cropped_img = img[top_left_x:bottom_right_x, top_left_y:bottom_right_y]
    wid = cropped_img.shape[1]
    hei = cropped_img.shape[0]
    if hei>wid:
        cropped_img =cv2.rotate(cropped_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return cropped_img

def _cut_and_save_images(image_path, boxes, save_path):
    # 读取图片
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error loading image: {image_path}")
        return

    height, width = img.shape[:2]

    for idx, box in enumerate(boxes):
        x, y, w, h, confidence, angle = box
        # print(f"Processing box {idx}: {x}, {y}, {w}, {h}, {angle}")

        # 计算旋转矩阵
        M = cv2.getRotationMatrix2D((int(x), int(y)), -90+angle*180/np.pi, 1)

        # 计算旋转后图像的边界
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_width = int(height * sin + width * cos)
        new_height = int(height * cos + width * sin)

        # 调整旋转矩阵的平移部分，确保旋转后图像在新图像中居中
        M[0, 2] += (new_width / 2) - x
        M[1, 2] += (new_height / 2) - y

        # 旋转图像
        rotated_image = cv2.warpAffine(img, M, (new_width, new_height))

        if rotated_image is None or rotated_image.size == 0:
            print(f"Failed to rotate image for box {box}")
            continue

        # 获取旋转后的目标区域的中心坐标
        original_point = np.array([int(x), int(y), 1])  # 齐次坐标
        rotated_point = np.dot(M, original_point)

        x_rot = rotated_point[0]
        y_rot = rotated_point[1]

        # 在旋转后的图像中裁剪出目标区域
        cropped_img = _crop_image(rotated_image, int(x_rot), int(y_rot), int(w), int(h))

        if cropped_img.size == 0:
            # print(f"Invalid crop at ({x}, {y}, {w}, {h})")
            continue

        # 保存裁剪后的图像
        cropped_img = cv2.resize(cropped_img, (300,60))
        output_filename = os.path.join(save_path, f"equality{idx}.png")
        cv2.imwrite(output_filename, cropped_img)

def detect(image,user):
    """
    @param image: PIL.Image对象，输入的图片
    @param user: str, 用户名
    @return: PIL.Image对象，处理后的图片
    """
    if image is None:
        return None
    save_path =os.path.join("./user",user,'image')
    if os.path.exists(save_path):
        clear_folder(save_path)
    os.makedirs(save_path,exist_ok=True)
    #image是一个ndarray对象，需要转换为PIL对象，并保存
    pil_image = Image.fromarray(image)
    pil_image = pil_image.resize((640, 640))
    #保存图片到user
    pil_image.save(os.path.join(save_path,"detected_image.png"))
    #得到检测结果
    boxes = infer_nms_bboxes("model/best_fp16_640.onnx",os.path.join(save_path,"detected_image.png"))
    #分割并保存检测到的目标
    start_time = time.time()
    _cut_and_save_images(os.path.join(save_path,"detected_image.png"),boxes, save_path)
    end_time = time.time()

    print(f"分割耗时：{end_time - start_time:.2f}秒")
    #画出检测结果
    result_img = draw_nms_boxes(boxes,os.path.join(save_path,"detected_image.png"))
    #OCR识别
    process_split_image(user)
    #删去错误图像
    process_wrong_image(user)
    return result_img

def update_images(user:str):
    """
    更新网页的图片列表
    :return:
    """
    if os.path.exists(os.path.join("./user",user,"images_gallery.html")):
        os.remove(os.path.join("./user",user,"images_gallery.html"))
    html_path = generate_html(os.path.join("./user",user,"latest","image"),user)
    # with open(html_path, 'r', encoding='utf-8') as file:
    #     html_content = file.read()
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>可点击链接示例</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            a {{
                display: inline-block;
                background-color: #4CAF50; /* 背景色 */
                color: white; /* 字体颜色 */
                padding: 10px 20px; /* 内边距 */
                font-size: 18px; /* 字体大小 */
                text-decoration: none; /* 去掉下划线 */
                border-radius: 5px; /* 圆角 */
                transition: background-color 0.3s ease; /* 背景色过渡效果 */
            }}
            a:hover {{
                background-color: #45a049; /* 鼠标悬停时的背景色 */
            }}
        </style>
    </head>
    <body>
        <a href="http://127.0.0.1:5000/{user}" target="_blank">访问 {user} 的结果</a>
    </body>
    </html>
"""
    return html_content

def process_split_image(user:str):
    """

    对用户的图片进行OCR识别，并保存结果
    @param user: str, 用户名
    @return: str, 识别结果
    """
    #获取用户最新的图片
    image_path = os.path.join("./user",user,"image")
    #进行OCR识别
    file_list = get_all_file_paths(image_path)
    print(file_list)

    start_time = time.time()
    for img_path in file_list[1:]:
        ocr_and_save(user,img_path)
    end_time = time.time()
    print(f"OCR识别耗时：{end_time - start_time:.2f}秒")
    return "识别完成"

import os
import json
import time

def generate_html(image_folder, user):
    """
    生成展示用户结果的HTML生成器
    :param image_folder:
    :param user:
    :return:
    """
    # 获取图片文件的路径列表
    image_paths = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    # 初始化HTML内容
    html_content = """
        <div class="container">
    """

    # 生成每个图片和文本的HTML
    for filename in image_paths:
        image_url = f"{user}/image/{filename}"  # 使用Flask托管的路径
        U = user
        # 读取对应的JSON文件内容
        json_filename = os.path.join("user", user, "latest", "json", f"{filename.split('.')[0]}.json")
        print("json_filename:", json_filename)
        if os.path.exists(json_filename):
            with open(json_filename, "r", encoding="utf-8") as json_file:
                json_data = json.load(json_file)
                print(json_data)

                json_content = json_data.get("equality", "没有描述信息")  # 获取equality字段
                correct_value = json_data.get("correct", "unknown")# 获取correct字段
                result = json_data.get("result", "unknown")  # 获取result字段
        else:
            json_content = "没有找到对应的JSON文件"
            correct_value = "unknown"

        # 将 "correct" 字段值转换为中文并设置字体颜色
        if correct_value:
            correct_text = "正确"
            correct_color = "green"
            suppose_result = ""
        elif not correct_value:
            correct_text = "错误"
            correct_color = "red"
            suppose_result = "正确答案："+str(result)
        else:
            correct_text = "未知"
            correct_color = "gray"
            suppose_result = ""
        # 为每张图片创建一个包含图片、公式内容、是否正确和按钮的div容器
        html_content += f"""
        <div class="image-item">
            <img src="{image_url}" alt="{filename}">
            <div class="info">
                <p>{json_content}</p>  <!-- 显示JSON中equality字段的内容 -->
            </div>
            <div class="correct">
                <p style="color: {correct_color};">{correct_text}</p>  <!-- 显示“正确”或“错误”并添加字体颜色 -->
            </div>
            <div class="correct">
                <p style="color: {correct_color};">{suppose_result}</p>  <!-- 显示“正确”或“错误”并添加字体颜色 -->
            </div>
            <div>
                <button id="button-{filename}" onclick="callPythonFunction('{filename}', '{U}',this)">该公式计算正确</button>
            </div>
        </div>
        """

    # 关闭HTML标签
    html_content += """
        </div>
        <script>
            function callPythonFunction(imageName,user,button) {
                console.log('Python function called for ' + imageName);
                
                // 隐藏当前按钮
                button.style.display = 'none';
                
                fetch('/call_python_function', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({  image_name: imageName, user: user })
                })
                .then(response => response.json())
                .catch(error => console.error('Error:', error));
            }
        </script>
    </body>
    </html>
    """

    # 保存生成的HTML文件
    # html_file_path = os.path.join("user", user, "images_gallery.html")
    # with open(html_file_path, "w", encoding="utf-8") as f:
        # f.write(html_content)

    print("HTML 文件已生成！")
    return html_content


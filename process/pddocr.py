import json
import cv2
import os
import re
import concurrent.futures
from paddlex import create_model
from process.model import get_all_file_paths, clear_folder
import time

"""
该文件主要处理的是文字识别模块的纠错和公式判断结果的存储
"""

def preprocess_image(img_path, process=True):
    """
    处理分割的图像
    :param img_path: 输入图像的文件路径
    :param process: 是否进行图像处理，默认为True，表示进行处理
    :return: 处理后的图像或原图
    """
    # 读取图像
    ima = cv2.imread(img_path)

    # 如果不需要处理图像，直接返回原图
    if not process:
        return ima

    # 如果需要处理，执行以下操作
    denoised_img = cv2.medianBlur(ima, 3)
    # 转为灰度图
    gray_img = cv2.cvtColor(denoised_img, cv2.COLOR_BGR2GRAY)
    # 调整大小（根据需求，可以修改宽高）
    binary_img = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 5)
    resized_img_rgb = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2RGB)

    return resized_img_rgb

def save_ocr_result(res, img_save_path, json_save_path, index):
    """
    批量保存OCR结果到图片和JSON文件

    @param res: OCR模型输出
    @param img_save_path: 图片保存路径
    @param json_save_path: JSON保存路径
    @param index: 图片文件的索引
    """
    res.save_to_img(os.path.join(img_save_path, f"{index}.png"))
    res.save_to_json(os.path.join(json_save_path, f"{index}.json"))


#这个函数会被processImage.py调用，用来进行OCR识别并保存结果和图片到指定用户的latest文件夹
def ocr_and_save(user: str, img_path_list: list):
    """
    进行OCR识别并保存结果和图片到指定用户的latest文件夹

    @param user: str, 用户名
    @param img_path_list: list, 图片路径列表
    """
    PROCESS = False  # 是否进行图像处理，默认为False，表示不进行处理
    # 加载模型
    model = create_model("best_accuracy/inference")
    
    # 创建保存路径
    save_path = os.path.join("./user", user, "latest")
    img_save_path = os.path.join(save_path, "image")
    json_save_path = os.path.join(save_path, "json")

    # 一次性创建所有需要的文件夹
    os.makedirs(img_save_path, exist_ok=True)
    os.makedirs(json_save_path, exist_ok=True)

    # 使用线程池并行处理每个图片的预处理
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 对所有图片进行并行预处理
        preprocessed_images = list(executor.map(lambda img_path: preprocess_image(img_path, process=PROCESS), img_path_list))


    # 动态计算batch_size
    total_images = len(img_path_list)
    max_batch_size = 32  # 固定最大batch_size

    # 设置batch_size，如果图片数量小于最大阈值，则使用图片数量作为batch_size
    batch_size = min(max_batch_size, total_images)
    print(f"使用的batch_size: {batch_size}")

    # 批量输入到模型进行预测
    outputs_generator = model.predict(preprocessed_images, batch_size=batch_size)  # 动态调整batch_size

    # 使用线程池并行保存OCR结果
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        
        # 遍历处理后的图片和OCR输出结果
        for idx, (res, img_path) in enumerate(zip(outputs_generator, img_path_list)):
            img_name = os.path.basename(img_path)
            index, _ = os.path.splitext(img_name)

            # 将每个任务提交给线程池
            futures.append(executor.submit(save_ocr_result, res, img_save_path, json_save_path, index))

        # 等待所有任务完成
        for future in futures:
            future.result()  # 获取结果，确保所有任务都执行完

    return "识别完成"


def process_single_json(json_file_path):
    """
    处理单个 JSON 文件，进行 OCR 纠错
    """
    with open(json_file_path, 'r', encoding='GBK') as f:
        data = json.load(f)
    
    text = data["rec_text"]
    equality = convert_wrong_char(text)
    data["equality"] = "".join(equality)
    is_correct, res, equality_operator = equality_correct(equality)
    
    data["correct"] = (is_correct == "True")
    data["result"] = res
    data["equality_operator"] = equality_operator

    with open(json_file_path, 'w', encoding='GBK') as f:
        json.dump(data, f, indent=4)

    # 判断是否删除不合格图片和结果
    if data["rec_score"] < 0.7:
        os.remove(json_file_path)
        img_path = json_file_path.replace(".json", ".png")
        img_path_1 = img_path.replace("json", "image")
        os.remove(img_path_1)


def convert_wrong_char(equality: str) -> list:
    """
    将OCR识别的公式中的错误字符转换为正确字符,并返回正确结果的提示
    :param equality:
    :return: 一个含有公式字符串还有正确结果的数字型的列表
    """
    # 替换规则
    parts = re.split(r'([÷+\-x×X=])', equality)
    # 数字序列
    num_list = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    # 替换表
    trans_table = str.maketrans({
        "/": "1",
        "b": "6",
        "(": "1",
        ")": "7",
        "s": "5",
        "S": "5",
        "%": "4",
        "}": "1",
        "{": "1",
        "[": "1",
        "]": "1",
        "a": "0",
        "π": "=",
        "c": "5",
        "C": "5",
        " ": "",
        ":": ".",
        "D": "0",
        "O": "0",
        "o": "0",
        't': "4",
    })
    equality_list = [part.strip() for part in parts if part.strip()]
    for i, num in enumerate(equality_list):
        num = num.translate(trans_table)
        # 如果是数字，清理可能会出现前置或后置非数字字符
        if i in [0, 2, 4]:
            if len(num) > 1:
                if num[0] not in num_list:
                    num = num[1:]
                if num[-1] not in num_list:
                    num = num[:-1]
        equality_list[i] = num
    return equality_list


def equality_correct(equal_list: list):
    """
    返回一个公式是否正确的判断结果，还有公式其他信息的列表
    :param equal_list:
    :return:
    """
    print("is_correct?: ", equal_list)
    try:
        a, opr, b, _, res = equal_list
        a, b, res = eval(a), eval(b), eval(res)
    except (SyntaxError, ValueError, NameError) as e:
        print(f"Error in formula: {equal_list} -> {str(e)}")
        return "False", "识别错误", "unknown"

    output = "False"
    suppose = 0  # 应当的结果
    equal_operator = "unknown"
    threshold = 0.001  # 容许的浮点数误差
    if opr == '+':
        suppose = a + b
        equal_operator = "add"
        if abs(a + b - res) <= threshold:
            output = "True"
    elif opr == '-':
        suppose = a - b
        equal_operator = "minus"
        if abs(a - b - res) <= threshold:
            output = "True"
    elif opr in ['x', "X", "×"]:
        equal_operator = "mul"
        suppose = a * b
        if abs(a * b - res) <= threshold:
            output = "True"
    elif opr == '÷':
        equal_operator = "div"
        suppose = a / b
        if abs(a / b - res) <= threshold:
            output = "True"
    
    if isinstance(suppose, float):
        suppose = round(suppose, 5)
    return output, suppose, equal_operator

#这个函数会被processImage.py调用，用来对用户的图片进行OCR识别并保存结果
def process_wrong_image(user: str):
    """
    对用户的图片进行OCR识别，并保存结果
    @param user: str, 用户名
    """
    # 获取用户最新的图片
    json_path = os.path.join("./user", user, "latest", "json")
    json_list = get_all_file_paths(json_path)

    # 使用线程池并行处理多个 JSON 文件
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for j in json_list:
            futures.append(executor.submit(process_single_json, j))

        # 等待所有任务完成
        for future in futures:
            future.result()
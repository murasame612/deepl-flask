import json
import cv2
import os
import re
import concurrent.futures
from paddleocr import PaddleOCR
from process.model import get_all_file_paths

"""
该文件主要处理的是文字识别模块的纠错和公式判断结果的存储
"""

_ocr_model = None


def get_ocr_model():
    """
    懒加载 PaddleOCR 模型，避免重复初始化
    """
    global _ocr_model
    if _ocr_model is None:
        _ocr_model = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            ocr_version='PP-OCRv4',
        )
    return _ocr_model

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
    # 转为灰度图
    gray_img = cv2.cvtColor(ima, cv2.COLOR_BGR2GRAY)
    # 调整大小（根据需求，可以修改宽高）
    binary_img = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 5)
    resized_img_rgb = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2RGB)

    return resized_img_rgb

def _sorted_ocr_lines(ocr_result):
    """
    将OCR输出的文本框根据位置排序，便于拼接公式
    """
    if not ocr_result:
        return []

    def _center(box):
        xs = [point[0] for point in box]
        ys = [point[1] for point in box]
        return sum(ys) / len(ys), sum(xs) / len(xs)

    valid_lines = [
        line for line in ocr_result if isinstance(line, (list, tuple)) and len(line) >= 2
    ]
    if not valid_lines:
        return []

    return sorted(valid_lines, key=lambda item: _center(item[0]))


def _parse_ocr_output(ocr_result):
    """
    统一不同版本 PaddleOCR 的输出结构，返回识别文本和得分
    """
    texts = []
    scores = []

    if hasattr(ocr_result, "get"):
        rec_texts = ocr_result.get("rec_texts") or []
        rec_scores = ocr_result.get("rec_scores") or []
        texts = [t if isinstance(t, str) else t[0] for t in rec_texts]
        scores = rec_scores
    else:
        sorted_lines = _sorted_ocr_lines(ocr_result)
        for line in sorted_lines:
            text, score = line[1]
            if not text:
                continue
            texts.append(text.strip())
            scores.append(score)

    rec_text = "".join(texts)
    rec_score = sum(scores) / len(scores) if scores else 0.0
    return rec_text, rec_score


def save_ocr_result(ocr_result, img_save_path, json_save_path, index, src_img_path):
    """
    保存OCR结果到图片和JSON文件

    @param ocr_result: OCR模型输出
    @param img_save_path: 图片保存路径
    @param json_save_path: JSON保存路径
    @param index: 图片文件的索引
    @param src_img_path: 原始切割图片路径
    """
    rec_text, rec_score = _parse_ocr_output(ocr_result)

    json_data = {
        "rec_text": rec_text,
        "rec_score": rec_score
    }

    json_file = os.path.join(json_save_path, f"{index}.json")
    with open(json_file, 'w', encoding='GBK') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    # 复制原始切割图像，保持与JSON一致的文件名
    image = cv2.imread(src_img_path)
    if image is not None:
        cv2.imwrite(os.path.join(img_save_path, f"{index}.png"), image)
    else:
        print(f"警告: 无法读取原始图片 {src_img_path}")


#这个函数会被processImage.py调用，用来进行OCR识别并保存结果和图片到指定用户的latest文件夹
def ocr_and_save(user: str, img_path_list: list):
    """
    进行OCR识别并保存结果和图片到指定用户的latest文件夹

    @param user: str, 用户名
    @param img_path_list: list, 图片路径列表
    """
    PROCESS = False  # 是否进行图像处理，默认为False，表示不进行处理
    # 加载 PaddleOCR 模型
    ocr_model = get_ocr_model()
    
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


    # 使用最新的 PaddleOCR 模型逐张识别
    ocr_outputs = []
    for image in preprocessed_images:
        result = ocr_model.ocr(image)
        if isinstance(result, list):
            ocr_outputs.append(result[0] if result else [])
        else:
            ocr_outputs.append(result or [])

    # 使用线程池并行保存OCR结果
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        
        # 遍历处理后的图片和OCR输出结果
        for idx, (res, img_path) in enumerate(zip(ocr_outputs, img_path_list)):
            img_name = os.path.basename(img_path)
            index, _ = os.path.splitext(img_name)

            # 将每个任务提交给线程池
            futures.append(executor.submit(
                save_ocr_result,
                res,
                img_save_path,
                json_save_path,
                index,
                img_path
            ))

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

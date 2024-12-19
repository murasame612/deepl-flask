import onnxruntime as ort
import numpy as np
import cv2  # 用于读取和预处理图片（如果需要）

"""
ONNX 推理脚本。得到算术框并交给nms脚本处理
"""
def load_model(model_path):
    """
    加载 ONNX 模型并返回推理会话。
    """
    session = ort.InferenceSession(model_path)
    return session

def prepare_input(input_image_path,dtype):
    """
    读取并预处理输入图像以符合模型的输入要求。
    参数:
        input_image_path (str): 输入图像路径。
        input_shape (tuple): 输入数据的形状 (batch_size, channels, height, width)。

    返回:
        np.ndarray: 预处理后的输入数据。
    """
    # 读取图像
    img = cv2.imread(input_image_path)
    # 调整图像大小以匹配输入尺寸
    img_resized = cv2.resize(img, (640,640))  # (height, width)
    # 转换颜色格式从 BGR 到 RGB
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    # 归一化处理：0-255 -> 0-1
    if dtype == "float16":
        img_normalized = img_rgb.astype(np.float16) / 255.0
    elif dtype == "float32" :
        img_normalized = img_rgb.astype(np.float32) / 255.0
    else:
        raise TypeError

    img_transposed = np.transpose(img_normalized, (2, 0, 1))
    # 增加批量维度，变为 (batch_size, channels, height, width)
    input_data = np.expand_dims(img_transposed, axis=0)
    return input_data

def infer(session, input_data):
    """
    执行推理。
    参数:
        session (onnxruntime.InferenceSession): ONNX Runtime 推理会话。
        input_data (np.ndarray): 输入数据。

    返回:
        np.ndarray: 推理结果。
    """
    input_name = session.get_inputs()[0].name  # 获取输入节点名称
    output_name = session.get_outputs()[0].name  # 获取输出节点名称
    # 进行推理
    result = session.run([output_name], {input_name: input_data})
    return result[0]  # 假设只返回一个输出


def onnxinfer(model_path, input_image_path,d_type = 'float16'):
    """
    加载模型并执行推理。
    """
    # 加载 ONNX 模型
    session = load_model(model_path)

    # 准备输入数据
    input_data = prepare_input(input_image_path,d_type)

    # 执行推理
    result = infer(session, input_data)
    return result


import cv2
import numpy as np
from process.infel import onnxinfer
from shapely.geometry import Polygon

"""
非极大值抑制（NMS）算法，与processImage.py相协同使用
"""
def calculate_iou(box1, box2):
    """
    计算两个旋转矩形框的交并比（IoU）
    box: (x, y, w, h, confidence, angle)
    """
    def get_polygon(box):
        # 将旋转框转换为 cv2.boxes 格式 (center, size, angle)
        rect = ((box[0], box[1]), (box[2], box[3]), box[5] * (180 / np.pi))
        # 获取旋转框的四个顶点坐标
        points = cv2.boxPoints(rect)
        return Polygon(points)

    poly1 = get_polygon(box1)
    poly2 = get_polygon(box2)

    # 计算交集面积
    intersection_area = poly1.intersection(poly2).area
    if intersection_area == 0:
        return 0

    area1 = poly1.area
    area2 = poly2.area

    # 计算并集面积
    union_area = area1 + area2 - intersection_area
    return intersection_area / union_area

def nms(boxes, iou_threshold=0.5, score_threshold=0.7):
    """
    改进版极大抑制（NMS）算法
    boxes: 每个框的 (x, y, w, h, confidence, angle)
    iou_threshold: IOU阈值，重叠度超过此阈值则认为是重复框
    score_threshold: 置信度阈值，小于此值的框会被丢弃
    """
    if len(boxes) == 0:
        return []

    # 只保留置信度大于阈值的框
    boxes = [box for box in boxes if box[4] >= score_threshold]

    # 按置信度排序（降序）
    boxes = sorted(boxes, key=lambda x: x[4], reverse=True)

    selected_boxes = []

    while boxes:
        # 选择置信度最高的框
        current_box = boxes.pop(0)
        selected_boxes.append(current_box)
        boxes = [
            box for box in boxes
            if calculate_iou(current_box, box) < iou_threshold
        ]

    return selected_boxes

def infer_nms_bboxes(md_path,input_ima_path,iou_threshold=0.5, score_threshold=0.7,d_type='float32',):
    prue_ret = onnxinfer(md_path, input_ima_path,d_type)
    boxes = list(prue_ret[0].T)
    nms_boxes_ret = nms(boxes,iou_threshold,score_threshold)
    return nms_boxes_ret

def draw_nms_boxes(nms_boxes_in,input_image_path):
    image = cv2.imread(input_image_path)
    image = cv2.resize(image, (640, 640))
    for box in nms_boxes_in:
        x, y, w, h, confidence, angle = box
        angle_deg = angle * (180 / np.pi)  # 将角度从弧度转换为度数
        rect = ((x, y), (w, h), angle_deg)  # 中心点 (x, y)，宽度 w，高度 h，旋转角度 angle
        box_points = cv2.boxPoints(rect)  # 计算旋转矩形框的四个顶点
        box_points = np.int_(box_points)  # 转换为整数坐标
        # 绘制旋转矩形框
        cv2.drawContours(image, [box_points], -1, (0, 255, 0), 2)
    return image

def convert_nms2normalized(nms_boxes_in):
    ret = []
    for box in nms_boxes_in:
        x, y, w, h, confidence, angle = box
        angle_deg = angle * (180 / np.pi)  # 将角度从弧度转换为度数
        rect = ((x, y), (w, h), angle_deg)  # 中心点 (x, y)，宽度 w，高度 h，旋转角度 angle
        box_points = cv2.boxPoints(rect)  # 计算旋转矩形框的四个顶点
        for xy in box_points:# 转换为整数坐标
            xy[0]=xy[0]/640
            xy[1]=xy[1]/640
        ret.append(box_points)
    return ret

from PIL import Image

if __name__ == "__main__":
    nms_boxes = infer_nms_bboxes("model/best_fp16_640.onnx", "user/100_aug_0.jpg")
    img = draw_nms_boxes(nms_boxes, "user/100_aug_0.jpg")
    img = Image.fromarray(img)
    for i in nms_boxes:
        print(i[:5],i[5]*(180/np.pi))

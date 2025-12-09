## 基于 yolo 分割的目标检测, paddle OCR 的识别系统

本项目使用 flask 框架搭建了一个简单的 web 服务, 实现了基于 yolo 分割的目标检测和 paddle OCR 的识别功能.

### 安装依赖

```bash
pip install -r requirements.txt
```
### 运行服务

```bash
python main.py
```

### 使用说明
启动服务后, 可以通过浏览器访问 `http://localhost:5000` 来使用该系统. 上传图片后, 系统会返回检测和识别的结果.

### 配置参数
- `threshold`: 目标检测的置信度阈值, 默认为 0.2, 可以根据需要进行调整, 在[main.py](main.py)中修改.

### 需要将 OCR 模型
将 OCR 模型拷贝到" best_accuracy/inference "目录下

### 最后
这是我和我朋友一起完成的一个小项目, 如果能帮助到你的大作业, 请给一个 star 。


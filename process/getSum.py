import json
import os
from process.model import get_all_file_paths
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题


def save_in_user(user: str):
    # Ensure the directory exists
    user_dir = os.path.join("user", user, "history")
    os.makedirs(user_dir, exist_ok=True)

    history_path = os.path.join(user_dir, "his.json")
    json_list = get_all_file_paths(f"user/{user}/latest/json")  # Ensure get_all_file_paths is defined

    e_sum = len(json_list)
    correct_sum = 0
    mul_sum = 0
    div_sum = 0
    add_sum = 0
    minus_sum = 0
    mul_correct_sum = 0
    div_correct_sum = 0
    add_correct_sum = 0
    minus_correct_sum = 0
    wrong_equality_list = []

    # Analyze the JSON files in the "latest" folder
    for j_path in json_list:
        with open(j_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Operator-based counting
        if data["equality_operator"] == "mul":
            mul_sum += 1
            if data["correct"]:
                mul_correct_sum += 1
                correct_sum += 1
        elif data["equality_operator"] == "div":
            div_sum += 1
            if data["correct"]:
                div_correct_sum += 1
                correct_sum += 1
        elif data["equality_operator"] == "add":
            add_sum += 1
            if data["correct"]:
                add_correct_sum += 1
                correct_sum += 1
        elif data["equality_operator"] == "minus":
            minus_sum += 1
            if data["correct"]:
                minus_correct_sum += 1
                correct_sum += 1

        # Collect wrong answers
        if not data["correct"]:
            wrong_equality_list.append([data['equality'], str(data['result'])])  # Fix spelling

    # Check if the history file exists
    if not os.path.exists(history_path):
        history_data = {
            "total": e_sum,
            "correct": correct_sum,
            "div_sum": div_sum,
            "add_sum": add_sum,
            "mul_sum": mul_sum,
            "minus_sum": minus_sum,
            "div_correct_sum": div_correct_sum,
            "add_correct_sum": add_correct_sum,
            "mul_correct_sum": mul_correct_sum,
            "minus_correct_sum": minus_correct_sum,
            "wrong_equality_list": wrong_equality_list
        }
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=4)
    else:
        with open(history_path, 'r', encoding='utf-8') as f:
            his = json.load(f)

        # Update existing history data
        his["total"] += e_sum
        his["correct"] += correct_sum
        his["div_sum"] += div_sum
        his["add_sum"] += add_sum
        his["mul_sum"] += mul_sum
        his["minus_sum"] += minus_sum
        his["div_correct_sum"] += div_correct_sum
        his["add_correct_sum"] += add_correct_sum
        his["mul_correct_sum"] += mul_correct_sum
        his["minus_correct_sum"] += minus_correct_sum
        his['wrong_equality_list'].extend(wrong_equality_list)

        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(his, f, indent=4)

def gen_ala_html(user: str):
    # 读取 JSON 文件
    if os.path.exists(f"user/{user}/history/his.json"):
        with open(f"user/{user}/history/his.json", 'r', encoding='utf-8') as f:
            his = json.load(f)
    else:
        return "<p>你还没有提交记录</p>"
        
    # 计算正确率
    acc = his["correct"] / his["total"]
    add_acc = "无数据" if his["add_sum"] == 0 else his["add_correct_sum"] / his["add_sum"] * 100
    div_acc = "无数据" if his["div_sum"] == 0 else his["div_correct_sum"] / his["div_sum"] * 100
    mul_acc = "无数据" if his["mul_sum"] == 0 else his["mul_correct_sum"] / his["mul_sum"] * 100
    minus_acc = "无数据" if his["minus_sum"] == 0 else his["minus_correct_sum"] / his["minus_sum"] * 100
    acc *= 100

    label_list = ['加法', '减法', '乘法', '除法'] 
    correct_sum_list = [his['add_correct_sum'], his['minus_correct_sum'], his['mul_correct_sum'], his['div_correct_sum']]
    sum_list = [his['add_sum'], his['minus_sum'], his['mul_sum'], his['div_sum']]
    # 绘制饼图
    labels = [label_list[i] for i in range(4) if sum_list[i] > 0]
    sizes = [correct_sum_list[i] for i in range(4) if sum_list[i] > 0]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # 使饼图为圆形
    plt.title("各题目正确率分布")

    # 保存饼图
    pie_chart_path = f"user/{user}/history/pie_chart.jpg"
    plt.savefig(pie_chart_path,dpi=300)
    plt.close()

    # 创建 HTML 内容
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>批改结果展示</title>
</head>
<body>
    <h3>批改结果展示</h3>
    
    <p>您总共计算了<strong>{his["total"]}</strong>道题目，正确率为<strong>{acc:.2f}%</strong>。</p>
        
    <p>题目统计：</p>
    {f"<p>加法题目总数：<strong>{his['add_sum']}</strong>道，做对的题目数：<strong>{his['add_correct_sum']}</strong>道，正确率：<strong>{add_acc:.2f}%</strong></p>" if his["add_sum"] > 0 else ""}
    {f"<p>除法题目总数：<strong>{his['div_sum']}</strong>道，做对的题目数：<strong>{his['div_correct_sum']}</strong>道，正确率：<strong>{div_acc:.2f}%</strong></p>" if his["div_sum"] > 0 else ""}
    {f"<p>乘法题目总数：<strong>{his['mul_sum']}</strong>道，做对的题目数：<strong>{his['mul_correct_sum']}</strong>道，正确率：<strong>{mul_acc:.2f}%</strong></p>" if his["mul_sum"] > 0 else ""}
    {f"<p>减法题目总数：<strong>{his['minus_sum']}</strong>道，做对的题目数：<strong>{his['minus_correct_sum']}</strong>道，正确率：<strong>{minus_acc:.2f}%</strong></p>" if his["minus_sum"] > 0 else ""}
 
    <p>该结果是根据您的历史数据计算得出的。</p>
    
    <!-- 插入饼图 -->
    <img src="http://127.0.0.1:5000/{user}/history/pie_chart.jpg" width="300" height="300" alt='图片加载失败' align='center'>
</body>
</html>
    """
    
    return html_content


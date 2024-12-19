from openai import OpenAI
import json
import markdown

def get_wrong_equation(user: str):
    history_path = f"user/{user}/history/his.json"  # 文件路径
    
    # 读取 JSON 文件
    with open(history_path, 'r', encoding='utf-8') as f:
        data = json.load(f)  # 将文件内容加载为 Python 字典
    
    # 处理数据
    wrong_equality_list = data['wrong_equality_list']  # 获取错误等式列表
    if wrong_equality_list == []:  # 如果列表为空，则返回提示信息
        return "暂无错误等式记录，请继续努力！"
    else:  # 如果列表不为空，则返回连接后的内容
        content_list = ['算式'+str(i+1)+': '+user+'计算'+wrong_equality_list[i][0]+'，但正确答案是'+wrong_equality_list[i][1]+'。' for i in range(len(wrong_equality_list))]  # 构造提示信息列表
        content = '\n'.join(content_list)  # 将列表内容用换行符连接
    return content  # 返回连接后的内容


def chat(user:str):

    content = get_wrong_equation(user)
    if content == "暂无错误等式记录，请继续努力！":
        result = content
    else:

        client = OpenAI(api_key="sk-c5690d7416634493b319358516ddb5c4", base_url="https://api.deepseek.com")

        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                        "role": "system",
                        "content": '''
        ```markdown
        **提示词：小学生算式错误分析专家**

        **定位：**
        - 专门针对小学生的算式错误进行分析和解释的智能助手。

        **能力：**
        - 能够识别和分析小学生在数学算式中常见的错误类型。
        - 提供详细的错误原因解释和正确的解题步骤。
        - 使用简单易懂的语言，帮助小学生理解和纠正错误。

        **知识储备：**
        - 熟悉小学数学课程标准和常见算式类型。
        - 掌握小学生在加减乘除、分数、小数等基础运算中常见的错误模式。
        - 了解教育心理学，能够以鼓励和建设性的方式进行反馈。

        **输入示例：**
        - **算式1**: 小红计算12÷4=5，但正确答案是3。  
        - **算式2**: 小红计算5×6=35，但正确答案是5。 
        - **算式3**: 小红计算1/2+1/3=2/5，但正确答案是5/6。  
        - **算式4**: 小红计算7.5+2.25=9.5，但正确答案是9.75。
        
        **模型任务：**
        根据每个算式和正确答案，分析并解释小学生可能出现的错误原因，提供详细的解题步骤和建议，帮助学生纠正错误。请以易懂的语言做出解释。
        ```
        '''
                },
                {
                        "role": "user",
                        "content": content
                }
            ]
        )
    # 获取分析结果
    result = completion.choices[0].message.content
    data = {}

    # 生成历史文件路径
    history_path = f"user/{user}/history/LLM_analysis.json"

    # 将 Markdown 格式的结果转换为 HTML
    result_html = markdown.markdown(result)

    # 读取现有的 JSON 文件并更新数据
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)  # 读取文件内容（如果文件已存在）
    except FileNotFoundError:
        # 如果文件不存在，初始化一个空字典
        data = {}

    # 将 HTML 格式的内容存储到字典中
    data['LLM_analysis'] = result_html

    # 将更新后的数据写回到 JSON 文件
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # 创建 HTML 内容
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能分析结果</title>
</head>
<body>
    <h1>智能分析结果</h1>
    <div>{result_html}</div>  <!-- 使用 div 来显示 HTML 内容 -->
</body>
</html>
    """

    return html_content



from openai import OpenAI
import json
import markdown
import threading

def get_wrong_equation(user: str):
    history_path = f"user/{user}/history/his.json"
    
    # 读取 JSON 文件
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return "没有历史记录！"
    
    wrong_equality_list = data['wrong_equality_list']
    if wrong_equality_list == []:
        return "您已经作对全部题目，请继续努力！"
    else:
        return wrong_equality_list

def process_single_equation(equation: str, correct_answer: str, user: str):
    client = OpenAI(api_key="sk-c5690d7416634493b319358516ddb5c4", base_url="https://api.deepseek.com")

    # 设置系统提示和用户输入内容
    content = f"算式: {equation}，但正确答案是{correct_answer}。"
    
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
                    **模型任务：**
                    根据每个算式和正确答案，分析并解释小学生可能出现的错误原因，提供详细的解题步骤和建议，帮助学生纠正错误。
                    ```
                '''
            },
            {
                "role": "user",
                "content": content
            }
        ]
    )

    result = completion.choices[0].message.content
    result_html = markdown.markdown(result)
    
    # 生成历史文件路径并保存分析结果
    history_path = f"user/{user}/history/LLM_analysis.json"
    data = {}

    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data[equation] = result_html

    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return result_html

def chat(user: str):
    wrong_equality_list = get_wrong_equation(user)
    
    if wrong_equality_list == "您已经作对全部题目，请继续努力！":
        return wrong_equality_list

    # 使用多线程遍历每个算式并调用 `process_single_equation`
    threads = []
    results = []

    def process_thread(equation, correct_answer):
        result = process_single_equation(equation, correct_answer,user)
        results.append(result)

    for equation, correct_answer in wrong_equality_list:
        thread = threading.Thread(target=process_thread, args=(equation, correct_answer))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    return results



import os
import shutil

"""
该文件处理一些文件的寻找和清理操作
"""
def generate_html_with_images(image_paths):
    html_content = '<div class="image-container">'
    for path in image_paths:
        # 使用绝对路径
        abs_path = os.path.abspath(path)
        html_content += f'<img src="file://{abs_path}" style="margin: 10px; max-width: 200px; max-height: 200px;">'
    html_content += '</div>'
    return html_content

def get_image_paths(user):
    # 获取用户目录下的所有图片路径
    user_dir = os.path.join("./user", user, 'image')
    if not os.path.exists(user_dir):
        return []
    return [os.path.join(user_dir, img) for img in os.listdir(user_dir) if img.endswith(('.png', '.jpg', '.jpeg'))]

def get_all_file_paths(directory):
    """
    获取指定目录下所有文件的路径，递归遍历子目录。

    :param directory: 要遍历的目录路径
    :return: 包含所有文件路径的列表
    """
    file_paths = []  # 存储文件路径的列表

    # 遍历指定目录及其子目录
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 获取文件的完整路径
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths

def clear_folder(folder_path):
    # 确保文件夹存在
    if os.path.exists(folder_path):
        # 遍历文件夹中的所有内容
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                # 如果是目录，递归清空目录
                shutil.rmtree(item_path)
            else:
                # 如果是文件，直接删除
                os.remove(item_path)

def delete_his_json(user:str):
    if os.path.exists(f"user/{user}/history/his.json"):
        os.remove(f"user/{user}/history/his.json")
        return "<p>已删除历史记录</p>"
    else:
        return "<p font_colour=\"red\">无历史记录</p>"

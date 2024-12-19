import csv

# 读取CSV文件的函数
def read_accounts_from_csv(csv_file):
    accounts = {}
    try:
        with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # 跳过标题行
            for row in reader:
                username, password = row
                accounts[username] = password
    except FileNotFoundError:
        print(f"文件 {csv_file} 未找到。")
    return accounts


def add_account_to_csv(csv_file, username, password):
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([username, password])
        print(f"账号 {username} 已添加成功！")
    except Exception as e:
        print(f"发生错误: {e}")

# 验证用户输入的账号密码
def verify_account(accounts, username, password):
    if username in accounts:
        if accounts[username] == password:
            return True
        else:
            print("密码错误！")
            return False
    else:
        print("账号不存在！")
        return False

# 示例：如何使用这些函数
if __name__ == '__main__':
    csv_file = 'accounts.csv'

    # 读取CSV文件中的账号密码
    accounts = read_accounts_from_csv(csv_file)

    # 用户注册（添加账号和密码）
    # 注意：这里直接添加密码作为明文，为了更安全，密码应使用哈希加密处理
    add_account_to_csv(csv_file, 'user4', 'password4')

    # 用户登录验证
    username_input = input("请输入用户名: ")
    password_input = input("请输入密码: ")

    if verify_account(accounts, username_input, password_input):
        print("登录成功！")
    else:
        print("登录失败！")
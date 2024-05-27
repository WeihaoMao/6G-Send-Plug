from flask import Flask, request, jsonify
import json
import pymysql.cursors
import Begin
import os
import base64
import subprocess
import glob

app = Flask(__name__)

# MySQL 数据库连接配置
MYSQL_HOST = 'w6109r6604.goho.co'
MYSQL_PORT = 10195
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'password'
MYSQL_DB = 'data'

#创建自己的项目名称
my_project_name = "slice"

# 建立 MySQL 数据库连接
connection = pymysql.connect(host=MYSQL_HOST,
                             port=MYSQL_PORT,
                             user=MYSQL_USER,
                             password=MYSQL_PASSWORD,
                             db=MYSQL_DB,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


def save_files_in_directory_to_db(directory):
    from datetime import datetime
    # 获取当前时间
    current_time = datetime.now()

    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode('utf-8')
            with connection.cursor() as cursor:
                insert_query = "INSERT INTO program_output (program_setting_time, filename, content) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (current_time, file, file_content))
            connection.commit()


@app.route('/generate_data', methods=['POST'])
def generate_data():
    try:
        data = request.get_json()  # 获取 POST 请求中的 JSON 数据
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # 将 JSON 数据写入文件
        with open('data.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        # 将 JSON 数据写入 MySQL 数据库
        with connection.cursor() as cursor:
            # 创建表
            create_table_query = """
            CREATE TABLE IF NOT EXISTS program (
                program_setting_time TEXT,
                data TEXT,
                name VARCHAR(255)
                
            )
            """
            cursor.execute(create_table_query)

            from datetime import datetime

            # 获取当前时间
            current_time_begin = datetime.now()

            # 插入数据
            insert_query = "INSERT INTO program (program_setting_time, data, name) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (current_time_begin, json.dumps(data), my_project_name))

        # 提交更改
        connection.commit()

        #！！调用主程序位置：
        # Begin.main() 这个方法弃掉 容易出现内存泄漏！
        subprocess.run(["python", "Begin.py"])

        #将data中的output.png和txt存入数据库：
        with connection.cursor() as cursor:
            # 创建表
            create_table_query = """
            CREATE TABLE IF NOT EXISTS program_output (
                program_begin_time TEXT,
                program_end_time TEXT,
                filename TEXT,
                content LONGTEXT,
                name VARCHAR(255)
            )
            """
            cursor.execute(create_table_query)
            current_time_end = datetime.now()
            #directory为输出路径
            directory = 'data'
            files = os.listdir(directory)
            for file in files:
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):
                    with open(file_path, 'rb') as f:
                        file_content = base64.b64encode(f.read()).decode('utf-8')
                    with connection.cursor() as cursor:
                        insert_query = "INSERT INTO program_output (program_begin_time, program_end_time, filename, content, name) VALUES (%s, %s, %s, %s, %s)"
                        cursor.execute(insert_query, (current_time_begin, current_time_end, file, file_content, my_project_name))
                    connection.commit()

            for file in glob.glob("./data/*"):
                os.remove(file)
                print("Deleted " + str(file))
            for file in glob.glob("./pic/*"):
                os.remove(file)
                print("Deleted " + str(file))
        return jsonify({'message': 'JSON data stored in file and MySQL successfully'}), 200






    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

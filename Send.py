from flask import Flask, request, jsonify
import json
import pymysql.cursors
import Begin
import os
import base64
import subprocess
import glob
import logging
from contextlib import redirect_stdout, redirect_stderr
from io import TextIOWrapper
from threading import Thread
import time

app = Flask(__name__)

#是否debug，打包镜像时请置为False
debug=True
# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
    logging.StreamHandler(), # 输出到终端
    logging.FileHandler('./app.log') # 输出到文件
    ]
)

# 定义全局变量用来控制线程是否继续运行
runningThread = True

# MySQL 数据库连接配置
MYSQL_HOST = '10.193.166.100'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASSWORD = '123123'
MYSQL_DB = 'view_5g_data_product'

#创建自己的项目名称
my_project_name = "slice202407"

# 建立 MySQL 数据库连接
connection = pymysql.connect(host=MYSQL_HOST,
                             port=MYSQL_PORT,
                             user=MYSQL_USER,
                             password=MYSQL_PASSWORD,
                             db=MYSQL_DB,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

# 将所有的 print() 语句重定向到日志记录器
class LoggingIOWrapper(TextIOWrapper):
    def init(self, stream, **kwargs):
        super().init(stream, **kwargs)
    def write(self, msg):
        for line in msg.rstrip().split('\n'):
            if line.strip():  # 检查行是否为空字符串
                logging.info(line)

    def flush(self):
        pass
def stream_output(stream, log_file):
    global runningThread
    while runningThread:
        line = stream.readline()
        if not line:
            break
        log_file.write(line)

log_s=""
def update_log(current_time_begin):
    global runningThread
    while runningThread:
        time.sleep(1) # 每 1 秒更新一次
        with connection.cursor() as cursor:
            with open('./app.log', 'r', encoding='utf-8', errors='ignore') as log_file:
                log_s = log_file.read()
            # 插入数据
            try:
                update_query = "UPDATE program_log SET log = %s WHERE program_begin_time = %s"
                if connection is not None:
                    print(log_s,current_time_begin)
                    cursor.execute(update_query, (log_s, current_time_begin))
                    connection.commit()
            except pymysql.Error as e:
                print(f"MySQL Error: {e}")
        print("此处更新log"+update_query)



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


@app.route('/post_json', methods=['POST'])
def generate_data():
    try:
        data = request.get_json()  # 获取 POST 请求中的 JSON 数据
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # 将 JSON 数据写入文件
        with open('data.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

        from datetime import datetime
        # 获取当前时间
        current_time_begin = datetime.now()
        # 将 JSON 数据写入 MySQL 数据库
        with connection.cursor() as cursor:
            # 插入数据
            insert_query = "INSERT INTO program (program_setting_time, data, name) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (current_time_begin, json.dumps(data), my_project_name))

            insert_log_query = "INSERT INTO program_log (program_begin_time, log, isEnd) VALUES (%s, %s, %s)"
            cursor.execute(insert_log_query, (current_time_begin, "NULL", 0))
        # 提交更改
        connection.commit()

        # ！！调用主程序位置：
        # Begin.main() 这个方法弃掉 容易出现内存泄漏！
        with open('./app.log', 'w') as file:
            file.truncate(0)
        # 将 stdout 和 stderr 重定向到 LoggingIOWrapper
        # 将 stdout 和 stderr 重定向到 LoggingIOWrapper
        with open('./app.log', 'w', encoding='utf-8', newline='') as log_file:
            wrapper = LoggingIOWrapper(log_file, encoding='utf-8')
            proc = subprocess.Popen(["python", "Begin.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    encoding='utf-8')
            global runningThread
            runningThread = True
            # 创建线程实时读取子进程的输出并写入日志文件
            stdout_thread = Thread(target=stream_output, args=(proc.stdout, wrapper))
            stderr_thread = Thread(target=stream_output, args=(proc.stderr, wrapper))
            stdout_thread.start()
            stderr_thread.start()

            # 创建线程定期更新
            update_log_thread = Thread(target=update_log, args=(current_time_begin,))
            update_log_thread.start()

            # 等待子进程完成
            proc.wait()

            runningThread = False
            # 等待线程结束,必须得加，否则子进程会延时完成，影响主进程操作数据库
            stdout_thread.join()
            stderr_thread.join()
            update_log_thread.join()

        #将data中的output.png和txt存入数据库：
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
                print("&&&&&向数据库存入"+file)
                connection.commit()
        if debug:
            for file in glob.glob("./data/*"):
                os.remove(file)
                print("Deleted " + str(file))
            for file in glob.glob("./pic/*"):
                os.remove(file)
                print("Deleted " + str(file))
        with connection.cursor() as cursor:
            update_query = "UPDATE program_log SET isEnd=1 WHERE program_begin_time = %s"
            cursor.execute(update_query, (current_time_begin,))
        connection.commit()
        return jsonify({'message': 'JSON data stored in file and MySQL successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/post_file', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 添加到pic文件下进行使用

    filename = file.filename
    filepath = os.path.join('pic', filename)
    file.save(filepath)
    with connection.cursor() as cursor:
        from datetime import datetime

        # 获取当前时间
        current_time_begin = datetime.now()

        # 插入数据
        insert_query = "INSERT INTO program (program_setting_time, data, name) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (current_time_begin, filename, my_project_name))
        connection.commit()

    subprocess.run(["python", "video.py"])

    try:
        current_time_end = datetime.now()
        # directory为输出路径
        directory = 'data'
        files = os.listdir(directory)
        for file in files:
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    file_content = base64.b64encode(f.read()).decode('utf-8')
                with connection.cursor() as cursor:
                    insert_query = "INSERT INTO program_output (program_begin_time, program_end_time, filename, content, name) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(insert_query,
                                   (current_time_begin, current_time_end, file, file_content, my_project_name))
                connection.commit()
        return jsonify({'success': 'File uploaded and filename stored in database'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

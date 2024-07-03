import requests

url = 'http://127.0.0.1:5000/post_file'
file_path = 'D:/1.mp4'

with open(file_path, 'rb') as file:
    files = {'file': file}
    response = requests.post(url, files=files)

print(response.json())

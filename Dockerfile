FROM python:3.7
WORKDIR ./slicesim
ADD . .
EXPOSE 5000
ENV TZ=Asia/Shanghai
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
CMD ["python", "./Send.py"] 

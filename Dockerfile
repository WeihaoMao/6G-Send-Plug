FROM python:3.7
WORKDIR ./slicesim
ADD . .
EXPOSE 5000
ENV TZ=Asia/Shanghai
# 设置环境变量，以便后续安装中文字体
ENV LANG C.UTF-8

# 安装中文字体
RUN apt-get update && apt-get install -y \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-arphic-ukai \
    fonts-arphic-uming
RUN apt-get update && apt-get install -y fonts-liberation

# 将simhei字体文件复制到镜像中
COPY simhei.ttf /usr/share/fonts/simhei.ttf

# 设置中文字体环境变量
ENV LANG C.UTF-8
ENV LANGUAGE C.UTF-8
ENV LC_ALL C.UTF-8

# 更新字体缓存
RUN fc-cache -f -v

RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
CMD ["python", "./Send.py"]


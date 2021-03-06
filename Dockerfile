FROM python:3.7

LABEL user="zuowei"
LABEL email="zuowei@yuchen.com"
LABEL version="1.0"
LABEL description="基于python3.7的scrapy采集程序"
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        git \
    && apt-get clean \
    && rm -r /var/lib/apt/lists/* 

# install package
COPY ./requirements.txt /
RUN pip3 --no-cache-dir install -r /requirements.txt \
    && rm -f /requirements.txt

# 终端设置
# 默认值是dumb，这时在终端操作时可能会出现：terminal is not fully functional
ENV LANG C.UTF-8
ENV TERM xterm
ENV PYTHONIOENCODING utf-8

# 解决时区问题
ENV TZ "Asia/Shanghai"

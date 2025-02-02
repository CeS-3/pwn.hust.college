FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive
ENV LC_CTYPE=C.UTF-8
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

RUN chmod 1777 /tmp
RUN sed -i.bak 's|https\?://archive.ubuntu.com|http://mirrors.hust.edu.cn|g' /etc/apt/sources.list
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        curl \
        wget \
        jq \
        iproute2 \
        iputils-ping \
        host \
        htop \
        gnupg \
        lsb-release \
        software-properties-common


RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list


RUN apt-get update && apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io


RUN mkdir -p /etc/docker
RUN echo '{"registry-mirrors": ["https://dockerpull.cn"], "data-root": "/opt/pwn.college/data/docker"}' > /etc/docker/daemon.json


RUN docker buildx install
RUN git clone --branch 3.6.0 https://github.com/CTFd/CTFd /opt/CTFd

RUN wget -O /etc/docker/seccomp.json https://gitee.com/mirrors/moby/raw/master/profiles/seccomp/default.json

RUN ln -s /opt/pwn.college/etc/systemd/system/pwn.college.service /etc/systemd/system/pwn.college.service
RUN ln -s /opt/pwn.college/etc/systemd/system/pwn.college.backup.service /etc/systemd/system/pwn.college.backup.service
RUN ln -s /opt/pwn.college/etc/systemd/system/pwn.college.backup.timer /etc/systemd/system/pwn.college.backup.timer
RUN ln -s /opt/pwn.college/etc/systemd/system/pwn.college.cachewarmer.service /etc/systemd/system/pwn.college.cachewarmer.service
RUN ln -s /opt/pwn.college/etc/systemd/system/pwn.college.cachewarmer.timer /etc/systemd/system/pwn.college.cachewarmer.timer
RUN ln -s /etc/systemd/system/pwn.college.service /etc/systemd/system/multi-user.target.wants/pwn.college.service
RUN ln -s /etc/systemd/system/pwn.college.backup.timer /etc/systemd/system/timers.target.wants/pwn.college.backup.timer
RUN ln -s /etc/systemd/system/pwn.college.cachewarmer.timer /etc/systemd/system/timers.target.wants/pwn.college.cachewarmer.timer

RUN mkdir -p /opt/pwn.college
ADD . /opt/pwn.college
RUN find /opt/pwn.college/dojo -type f -exec ln -s {} /usr/bin/ \;

EXPOSE 22
EXPOSE 80
EXPOSE 443
WORKDIR /opt/pwn.college
CMD ["dojo", "start"]

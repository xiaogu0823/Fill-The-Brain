# docker

### docker安装

~~~bash
# linux
curl -fsSL https://get.docker.com -o install-docker.sh
sudo sh install-docker.sh
# window
wsl --set-defualt-version 2

### command:  注册表/namespace/标签：版本号
docker pull docker.io/library/nginx:lastest

### 网络配置
sudo vi /etc/docker/daemon.json #添加配置
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev"
  ],
~~~

### common command
~~~bash
sudo service docker restart #重启程序拉取镜像
sudo docker image #查看
sudo docker rmi # 删除镜像
sudo docker pull --platfrom=xxx nginx #linux/arm64为例，指定cpu架构
sudo docker run -d/-p/-v 镜像名 #后台运行/端口映射(端口绑定 外：内)/绑定挂载（同步宿主机和容器目录）加-f force(强制删除容器)
sudo docker volume inspect 挂载卷名 
sudo docker volume prune -a #删除所有无容器使用的卷
sudo docker run -d --name 容器名 镜像名
sudo docker run -it --rm 轻量级镜像 #-it是指进入容器交互 --rm是容器停止就删除（这个指令用于临时调试） 
sudo docker run -d --restart always 镜像 #--restart容器停止会立刻重启,always换成unless-stopped手动停止容器不会重启
sudo docker stop/start
#参看容器中进程
docker exec id/容器名 接指令（如：ps -ef）
#在容器中安装东西需要先查看容器Linux发行版 cat /etc/os-release

~~~

##### dockerfile-example（自己打包项目镜像）

~~~bash
# 使用docker官方 Python基础镜像
FROM python:3.10-slim
# 设置工作目录
WORKDIR /app
# 复制应用代码
COPY ./app ./app #当前项目本地目录，容器目录
# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 暴露端口
EXPOSE 8000
# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
~~~

**dockerfile完成，执行以下操作构建镜像**

~~~bash
docker bulid -t 镜像名 . #当前目录创建
然后执行 docker run -d -p 8000:8000 镜像名
登录 docker login
推送镜像前要加直接的命名空间 docker build -t namespace/镜像名 .
docker push namespace/镜像名
~~~

~~~bash
### docker compose 管理多个容器，创建docker-comose.yaml标准名（自动同一个子网）这个适用于个人
vi docker-comose.yaml
sudo doker compose up/down -d #运行配置启动容器 ,down停止并删除，stop停止
非标准的文件名： sudo docker compose -f 文件 up -d 
~~~


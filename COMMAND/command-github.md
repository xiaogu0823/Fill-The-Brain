# gitlab/github

### 本地或服务器或设备项目上传gitlab（第一次）

**初始化-添加缓存，提交- 添加远程关联http（需要access token）或者ssh（需要配置密钥）-验证关联-创建分支，上传**

~~~bash
###日常指令
rm -rf .git(Linux/macOS) 或 rd /s .git(Windows) # 移除git， 重置仓库
# 全局配置（按顺序执行）
git config --global user.email 'guyuling@example.com'
git config --global user.name 'guyuling'
# 远程配置
git remote -v
git remote add origin https://github.com/xiaogu0823/Fill-The-Brain.git
git remote set-url origin git@github.com:xiaogu0823/Fill-The-Brain.git
git remote rm origin # 移除远程连接
### 配置使用ssh或者https
# ssh 配置后需要添加ssh密钥验证身份
ls -al ~/.ssh # 检查现有密钥 #生成新密钥
SHA256:sAUfRmnemWiJhIrm1C/JMuBgp9LoJA7cqfYk+5s74eI guyuling@example.com
eval "$(ssh-agent -s)"# 启动ssh-agent后台服务，避免每次都输入密钥 输出Agent pid 12789
# 将您的私钥添加到agent中（请将 ~/.ssh/id_ed25519 替换成您实际的私钥路径）
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub # 复制这个公钥文件中内容替换github账户

# 分支重命名
git branch -m new-branch-name
git push origin --delete old-name#删除分支

git branch -r # 查看远程分支列表
git fetch origin # 首先获取最新的远程信息
git push --set-upstream origin feature-xiaogu # 新分支推送远程仓库

git status # 查看当前修改状态
git log --oneline --graph --all # 查看提交历史
——————————————————————————————————————————————————
git checkout -b feature-api- origin/feature-xiaogu # 创建并切换到本地dev分支，跟踪远程dev分支（分支不在本地时）
git checkout dev # dev分支已存在本地
git pull origin dev 
——————————————————————————————————————————————————
git checkout -b feature-xiaogu master # 基于dev分支创建新分支（推荐方式）
git push -u origin feature-api # 将新分支推送到GitLab
————————————————————————————————————开发新功能时
git status # 查看当前修改状态
git add . # 进行代码修改后，添加更改到暂存区
git commit -m "描述您的修改内容" # 提交更改
git commit -m "feat: 添加xxx功能"（同上一句）
git push -u origin feature-xiaogu # 如果需要推送到远程仓库（协作时）(首次推送需要设置上游分支)
git push # 后续推送只需
——————————————————————————保存与dev分支同步
git checkout -b feature-xiaogu main # 定期将dev分支的最新更改合并到的分支
git fetch origin # 定期获取最新代码
git merge origin/dev # 将dev分支的最新更改合并到您的分支

# 或使用rebase（推荐用于功能分支）
git rebase origin/dev

#  拉取远程仓库的内容并允许不相关的历史记录（冲突解决）
git pull origin main --allow-unrelated-histories
~~~

[基于Gitlab的流程版本控制指南 - 知乎](https://zhuanlan.zhihu.com/p/449095926)

### huggfaceface-cli

~~~bash
huggingface-cli download --resume-download aicinema69/audio-emotion-detector-try2 --local-dir audio-emotion-detector-try2

~~~

[huggingface-cli下载数据（含国内镜像源方法）_huggingface-cli download-CSDN博客](https://blog.csdn.net/lanlinjnc/article/details/136709225)

### 镜像源

~~~bassh
-i https://pypi.tuna.tsinghua.edu.cn/simple 
~~~


lsof -i:8342
lsof -i:8342 | awk '{cmd="sudo kill -9 "$2; system(cmd)}'

lsof -i:7899
lsof -i:7899 | awk '{cmd="sudo kill -9 "$2; system(cmd)}'

lsof -i:7898
lsof -i:7898 | awk '{cmd="sudo kill -9 "$2; system(cmd)}'

lsof -i:7878
lsof -i:7878 | awk '{cmd="sudo kill -9 "$2; system(cmd)}'

# start
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/home/bjkj1/miniconda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/home/bjkj1/miniconda/etc/profile.d/conda.sh" ]; then
        . "/home/bjkj1/miniconda/etc/profile.d/conda.sh"
    else
        export PATH="/home/bjkj1/miniconda/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/root/miniconda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/root/miniconda/etc/profile.d/conda.sh" ]; then
        . "/root/miniconda/etc/profile.d/conda.sh"
    else
        export PATH="/root/miniconda/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

conda activate LLM

cd /disk2-7681G/users/guyuling/gradio_qwen

python /disk2-7681G/users/guyuling/gradio_qwen/assistant_web_test.py --share > test.out
# nohup python chat_gradio_qwen_full_version.py 2>&1 >> ./logs/chat_gradio_qwen_full_version.nohup &
# nohup python chat_gradio_qwen.py 2>&1 >> ./logs/chat_gradio_qwen.nohup &
# nohup python qwen_server_gradio.py 2>&1 >> ./logs/qwen_server_gradio.nohup &

# nohup python /home/bjkj1/disk2-7681G/users/chenxiuyan/MarketingAI/DeployModel/auto_test_checkpoints/auto_test.py 2>&1 >> ./logs/auto_test.nohup &

# nohup python /home/bjkj1/disk2-7681G/users/chenxiuyan/MarketingAI/DeployModel/auto_test_checkpoints/gradio_download_files.py 2>&1 >> ./logs/gradio_download_files.nohup &

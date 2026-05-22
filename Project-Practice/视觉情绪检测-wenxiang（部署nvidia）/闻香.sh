#!/bin/bash

source /home/nvidia/miniconda3/etc/profile.d/conda.sh

conda deactivate

cd /home/nvidia/workspace/wenxiang/

source /home/nvidia/wenxiang/bin/activate

python main.py

from volcenginesdkarkruntime import Ark
from dotenv import load_dotenv
from argparse import ArgumentParser
import json
import time
from loguru import logger
import os
import re


# 加载环境变量
load_dotenv()

system_prompt_value = os.getenv("singlePersonOralBroadcastingFromDoubao_system_prompt", "默认的系统提示内容")  # 如果找不到环境变量，使用默认值

DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")  
DOUBAO_MODEL_NAME = os.getenv("DOUBAO_MODEL_NAME")
DOUBAO_API_BASE = os.getenv("DOUBAO_API_BASE")

# 打印配置信息（生产环境可改用logger）
logger.info(f"DOUBAO_API_KEY: {DOUBAO_API_KEY}")
logger.info(f"DOUBAO_MODEL_NAME: {DOUBAO_MODEL_NAME}")
logger.info(f"DOUBAO_API_BASE: {DOUBAO_API_BASE}")

# 初始化Ark客户端
client = Ark(
    base_url=DOUBAO_API_BASE,
    api_key=DOUBAO_API_KEY,
)

def _get_args():
    parser = ArgumentParser()
    parser.add_argument("-c", "--checkpoint-path", type=str, help="Checkpoint name or path (not needed now)")
    parser.add_argument("--cpu-only", action="store_true", help="Run demo with CPU only")
    args = parser.parse_args()
    return args

# 添加1
def format_model_output(content):
    parts = content.split("## 脚本内容",1)
    
    if len(parts) < 2:
        return content
    script_idea = parts[0].strip()
    script_content = parts[1].strip()
          
    cleaned_script_content = re.sub(r"\n\w+：", " ", script_content) 
    cleaned_script_content = re.sub(r"\n", " ", cleaned_script_content).strip()

    formatted_output = f"{script_idea}\n## 脚本内容\n{cleaned_script_content}"
  
    return formatted_output

def generate_with_doubao_api(query, system_prompt, task_history, stream=False):
    # 构造聊天消息
    conversation = [{"role": "system", "content": system_prompt}]
    for query_h, response_h in task_history:
        conversation.append({"role": "user", "content": query_h})
        conversation.append({"role": "assistant", "content": response_h})
    
    conversation.append({"role": "user", "content": query})

    # 构造请求数据
    messages = conversation
    extra_headers = {'x-is-encrypted': 'true'}

    if stream:
        # 流式请求
        logger.info("----- streaming request_11 -----")
        stream = client.chat.completions.create(
            model=DOUBAO_MODEL_NAME,
            messages=messages,
            extra_headers=extra_headers,
            stream=True
        )
        full_response = ""
        for chunk in stream:
            if not chunk.choices:
                continue
            chunk_content = chunk.choices[0].delta.content
            if chunk_content:  # 仅在有内容时拼接
                full_response += chunk_content
            print(chunk_content, end="")

        # 格式化流式返回的内容
        full_response = format_model_output(full_response)
        logger.info(f"Streamed Full Response: {full_response}")

    else:
        # 非流式请求
        logger.info("----- standard request_22 -----")
        completion = client.chat.completions.create(
            model=DOUBAO_MODEL_NAME,
            messages=messages,
            extra_headers=extra_headers
        )
        print(f"模型回复{completion}")
        full_response = completion.choices[0].message.content

        print(f"输出内容：{full_response}")

        # 格式化非流式返回的内容
        full_response = format_model_output(full_response)
        print(full_response)  # 打印非流式响应内容

    return full_response

def generate_singlePersonOralBroadcastingFromDoubao(_productNameOrAdvertisingName, 
                                                    _description, 
                                                    _keywordsOrProductSellingPoints,
                                                    _WordNumber, 
                                                    _Qualificative,
                                                    _GuidanceWays,
                                                    _InitialMarketingStrategy,
                                                    _ActorRoles,
                                                    _TargetUsers,
                                                    _UserPainPoints, 
                                                    _ProductBenefits,
                                                    _ProductMarketingWays,
                                                    _singlePersonOralBroadcastingFromDoubaoSystemPrompt, 
                                                    _chatbot, 
                                                    _task_history, 
                                                    _titleOutput, stream=False):
    logger.info("-" * 10 + "\nDoubao-Chat: 单人口播")
    _system_prompt = _singlePersonOralBroadcastingFromDoubaoSystemPrompt
    _query = f"产品名称: {_productNameOrAdvertisingName}\n优惠活动: {_description}\n产品卖点: {_keywordsOrProductSellingPoints}\n文案字数:{_WordNumber}\n限制词:{_Qualificative}\n转化引导方式{_GuidanceWays}\开头营销策略:{_InitialMarketingStrategy}\n演员角色:{_ActorRoles}\n目标用户:{_TargetUsers}\n用户痛点:{_UserPainPoints}\n产品盈利点:{_ProductBenefits}\n产品营销方式:{_ProductMarketingWays}"
    _chatbot.append((_query, ""))

    full_response = ""
    response = ""
    titleOutput = {
        "systemPrompt": f"{_system_prompt}",
        "productName": f"{_productNameOrAdvertisingName}",
        "description": f"{_description}",
        "keywordsOrProductSellingPoints": f"{_keywordsOrProductSellingPoints}",
        "WordNumber": f"{_WordNumber}",
        "Qualificative": f"{_Qualificative}",
        "GuidanceWays": f"{_GuidanceWays}",
        "InitialMarketingStrategy": f"{_InitialMarketingStrategy}",
        "actorRoles" : f"{_ActorRoles}",
        "targetUsers": f"{_TargetUsers}",
        "userPainPoints": f"{_UserPainPoints}",
        "productBenefits": f"{_ProductBenefits}",
        "productMarketingWays": f"{_ProductMarketingWays}",
        "query": f"{_query}",
        "response": f"{full_response}"
    }

    start_time = time.time()
    response = generate_with_doubao_api(_query, _system_prompt, _task_history, stream)

    full_response = response
    _chatbot[-1] = (_query, response)
    titleOutput["response"] = response
    _titleOutput = json.dumps(titleOutput, indent=2, ensure_ascii=False)

    print(_titleOutput)  # 打印输出

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"---total_time---: {elapsed_time:.2f}")

    _task_history.append((_query, full_response))
    logger.info(f"History: {_task_history}")

def main():
    args = _get_args()

    # 示例：模拟输入数据进行模型调用
    chatbot = []
    task_history = []

    # 输入示例
    _productNameOrAdvertisingName = "巧克力"
    _description = "这是一个优惠活动"
    _keywordsOrProductSellingPoints = "特色卖点"
    _WordNumber = "简洁(50~150)"
    _Qualificative = "无"
    _GuidanceWays = "常规引导"
    _InitialMarketingStrategy = "卖点展示"
    _ActorRoles = "带货主播"
    _TargetUsers = "年轻女性"
    _UserPainPoints = "价格高"
    _ProductBenefits = "提升生活质量"
    _ProductMarketingWays = ["品牌宣传", "正话反说", "对比"]
    _singlePersonOralBroadcastingFromDoubaoSystemPrompt = system_prompt_value
    _titleOutput = ""

    # 调用模型进行响应
    generate_singlePersonOralBroadcastingFromDoubao(
        _productNameOrAdvertisingName, 
        _description, 
        _keywordsOrProductSellingPoints, 
        _WordNumber, 
        _Qualificative,
        _GuidanceWays,
        _InitialMarketingStrategy,
        _ActorRoles,  
        _TargetUsers, 
        _UserPainPoints, 
        _ProductBenefits,
        _ProductMarketingWays,
        _singlePersonOralBroadcastingFromDoubaoSystemPrompt, 
        chatbot, 
        task_history, 
        _titleOutput
    )

if __name__ == '__main__':
    main()

from volcenginesdkarkruntime import Ark
from dotenv import load_dotenv
from argparse import ArgumentParser
import gradio as gr
import json
import time
from loguru import logger
import os
import re

load_dotenv()  # 加载环境变量文件
# 获取系统提示内容，如果找不到环境变量则使用默认值
system_prompt_value = os.getenv("singlePersonOralBroadcastingFromDoubao_system_prompt", "默认的系统提示内容")

# 设置豆包API相关配置
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")  
DOUBAO_MODEL_NAME = os.getenv("DOUBAO_MODEL_NAME")
DOUBAO_API_BASE = os.getenv("DOUBAO_API_BASE")  
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
    parser.add_argument("--share", action="store_true", default=True, help="Create a publicly shareable link for the interface.")
    parser.add_argument("--inbrowser", action="store_true", default=False, help="Automatically launch the interface in a new tab on the default browser.")
    parser.add_argument("--server-port", type=int, default=8001, help="Demo server port.")
    parser.add_argument("--server-name", type=str, default="0.0.0.0", help="Demo server name.")

    args = parser.parse_args()
    return args

def process_script(input_str):
    # 分割输入字符串为各个部分
    parts = re.split(r'^\#{0,3} 脚本内容', input_str, flags=re.MULTILINE)
    # 保留脚本思路和脚本要求（字符串）
    befores_content = "\n".join(parts[0].split("\n"))
    
    script_part = parts[1].strip() if len(parts) > 1 else ""

    # 如果有脚本内容部分
    if len(parts) > 1:
        script_part = parts[1].strip()
        
        content = []
        for part in script_part.split("\n"):
            part = part.strip()
            if "：" in part:
                part = part.split("：")[1].strip()
                
                content.append(part)
            else:
                content.append(part.strip())
        script_content = "".join(content)
        # 输出整理后的格式，包含脚本内容
        output_str = befores_content + "\n## 脚本内容\n" + script_content
    else:
        # 如果没有脚本内容，直接将各部分拼接成脚本内容
        content = []
        for part in input_str.splitlines:
            if "## " in part:
                part = part.split("## ")[1].strip()
                if len(part) > 4:
                    part = part[4:]
                content.append(part.strip())
            else:

                content.append(part.strip())
        script_content = "".join(content)
        
        output_str = "\n## 脚本内容\n" + script_content

    return output_str

def generate_with_doubao_api(query, system_prompt, task_history, stream=False):
    """
    使用豆包API生成响应。
    参数:
        query (str): 查询字符串。
        system_prompt (str): 系统提示。
        task_history (list): 任务历史记录。
        stream (bool): 是否使用流式请求。
    返回:
        str: 生成的响应内容。
    """
    # 构造聊天消息
    conversation = [{"role": "system", "content": system_prompt}]  # 添加系统提示消息
    for query_h, response_h in task_history:  # 遍历任务历史记录并添加历史消息
        conversation.append({"role": "user", "content": query_h})  # 添加用户消息
        conversation.append({"role": "assistant", "content": response_h})  # 添加助手消息

    conversation.append({"role": "user", "content": query})  # 添加当前查询消息

    # 构造请求数据
    messages = conversation  # 将对话消息赋值给messages变量
    extra_headers = {'x-is-encrypted': 'true'}  # 设置额外请求头

    if stream:
        # 流式请求
        logger.info("----- standard request -----")  # 打印日志信息
        stream = client.chat.completions.create(
            model=DOUBAO_MODEL_NAME,  # 设置模型名称
            messages=messages,  # 设置消息内容
            extra_headers=extra_headers,  # 设置额外请求头
            stream=True  # 启用流式请求
        )
        full_response = ""  # 初始化完整响应内容
        for chunk in stream:  # 遍历流式响应数据块
            if not chunk.choices:  # 如果数据块没有选择项则跳过
                continue
            chunk_content = chunk.choices[0].delta.content  # 获取数据块内容
            full_response += chunk_content  # 累加到完整响应内容中
            print(chunk_content, end="")  # 打印流式响应内容
        print()  # 打印换行符
    else:
        # 非流式请求
        logger.info("----- 标准式输出 -----")  # 打印日志信息
        completion = client.chat.completions.create(
            model=DOUBAO_MODEL_NAME,  # 设置模型名称
            messages=messages,  # 设置消息内容
            extra_headers=extra_headers,  # 设置额外请求头
        )
        full_response = completion.choices[0].message.content  # 获取完整响应内容
        logger.info(f"整理前标准式输出{full_response}")
        full_response = process_script(full_response)
        logger.info(f"整理后标准式输出{full_response}")  # 打印非流式响应内容

    return full_response  # 返回生成的响应内容


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

    logger.info("-----" + "\n" + "DouChat-单人口播")  # 打印日志信息
    _system_prompt = _singlePersonOralBroadcastingFromDoubaoSystemPrompt
    _query = f"产品名称: {_productNameOrAdvertisingName}\n优惠活动: {_description}\n产品卖点: {_keywordsOrProductSellingPoints}\n文案字数:{_WordNumber}\n限制词:{_Qualificative}\n转化引导方式{_GuidanceWays}\开头营销策略:{_InitialMarketingStrategy}\n演员角色:{_ActorRoles}\n目标用户:{_TargetUsers}\n用户痛点:{_UserPainPoints}\n产品盈利点:{_ProductBenefits}\n产品营销方式:{_ProductMarketingWays}"
    _chatbot.append((_query, ""))  # 添加空响应到聊天机器人消息列表中

    full_response = ""  # 初始化完整响应内容
    response = ""  # 初始化响应内容
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
    
    start_time = time.time()  # 记录开始时间
    response = generate_with_doubao_api(_query, _system_prompt, _task_history, stream)
    logger.info(f"生成文案:{response} " )  # 打印任务历史记录日志信息



    full_response = response  # 更新完整响应内容
    _chatbot[-1] = (_query, response)  # 更新聊天机器人消息列表中的最后一个消息
    titleOutput["response"] = response  # 更新输出标题中的响应内容
    _titleOutput = json.dumps(titleOutput, indent=2, ensure_ascii=False)  # 将输出标题转换为JSON字符串格式

    end_time = time.time()  # 记录结束时间
    elapsed_time = end_time - start_time  # 计算运行时间
    logger.info(f"---total_time---: {elapsed_time:.2f}")  # 打印运行时间日志信息

    logger.info("History: " + str(_task_history))  # 打印任务历史记录日志信息

    _task_history.append((_query, full_response))  # 将查询和响应添加到任务历史记录中
    return _chatbot, _titleOutput  # 返回更新后的聊天机器人消息列表和输出标题

def _gc():
    """
    执行垃圾回收。
    """
    import gc
    gc.collect()  # 执行垃圾回收操作

def _launch_demo(args):
    """
    启动演示。
    参数:
        args (ArgumentParser对象): 命令行参数对象。
    """
    def reset_user_input():
        return gr.update(value="")

    def reset_state(_chatbot, _task_history):
        _task_history.clear()
        _chatbot.clear()
        _gc()
        return _chatbot

    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(label='DouChat-单人口播', elem_classes="control-height")  # 创建聊天机器人组件

        with gr.Tab("单人（豆包）口播"):
            productNameOrAdvertisingName = gr.Textbox(lines=2, label="产品名称", info="请输入产品名称")
            description = gr.Textbox(lines=2, label="优惠活动", info="请输入优惠活动")
            keywordsOrProductSellingPoints = gr.Textbox(lines=2, label="产品卖点", info="请输入产品卖点")
            WordNumber = gr.Radio(choices=["简洁(50~150)","正常(150~250)","丰富(250以上)"], label="文案字数(必填)", info="请选择文案字数")
            Qualificative = gr.Textbox(lines=2, label="限制词", info="请输入限制词(选填)")
            GuidanceWays = gr.Radio(choices=["常规引导","进入直播间","点击购买","评论区互动"], label="转化引导方式(选填)", info="请选择转化引导方式")
            InitialMarketingStrategy = gr.Radio(choices=["卖点展示","痛点直击","优惠突出","圈定人群","亲身体验","正话反说","设置悬念","错误示范","场景设定","热点话题","建议呼吁","品牌宣传","紧迫稀缺","地方特色","口碑好评","传统习俗","权威推荐","节庆礼品","对比","夸张","反问","道歉"], label="开头营销策略(必填)", info="请选择开头营销策略")
            ActorRoles = gr.Radio(choices=["好物推荐官","带货主播","产品员工","产品老板","专家","精致妈妈", "当家主妇", "上班族", "年轻女性","运动塑形人群","中年老人"], label="演员角色(单选)", info="请选择演员角色")
            TargetUsers = gr.Radio(choices=["精致妈妈", "当家主妇", "上班族", "年轻女性","运动塑形人群","中年老人"], label="目标用户(单选)", info="请选择目标用户")
            UserPainPoints = gr.Textbox(lines=2, label="用户痛点(选填)", info="请输入用户痛点")
            ProductBenefits = gr.Textbox(lines=2, label="产品盈利点(选填)", info="产品盈利点")
            ProductMarketingWays = gr.CheckboxGroup(choices=["圈定人群","亲身体验","正话反说","错误示范","场景设定","热点话题","建议呼吁","品牌宣传","紧迫稀缺","地方特色","口碑好评","传统习俗","权威推荐","节庆礼品","对比"],label="产品营销方式(最多选三个)", info="请选择产品营销方式")
            singlePersonOralBroadcastingFromDoubaoSystemPrompt = gr.Textbox(lines=2, label="系统提示", value=system_prompt_value)
            TitleOutput = gr.TextArea(label="输出（不需要输入）", lines=5, info="所有的变量信息")
            task_history = gr.State([])

            with gr.Row():
                empty_btn = gr.Button("🧹 Clear History (清除历史)")
                submit_btn = gr.Button("🚀 Submit (发送)")

            submit_btn.click(generate_singlePersonOralBroadcastingFromDoubao, 
                             [productNameOrAdvertisingName, 
                              description, 
                              keywordsOrProductSellingPoints, 
                              WordNumber, 
                              Qualificative,
                              GuidanceWays,
                              InitialMarketingStrategy,
                              ActorRoles,  
                              TargetUsers, 
                              UserPainPoints, 
                              ProductBenefits,
                              ProductMarketingWays,
                              singlePersonOralBroadcastingFromDoubaoSystemPrompt, 
                              chatbot, 
                              task_history, 
                              TitleOutput], [chatbot, TitleOutput], show_progress=True)
            submit_btn.click(reset_user_input, [], [productNameOrAdvertisingName])
            submit_btn.click(reset_user_input, [], [description])
            submit_btn.click(reset_user_input, [], [keywordsOrProductSellingPoints])
            submit_btn.click(reset_user_input, [], [WordNumber])
            submit_btn.click(reset_user_input, [], [Qualificative])
            submit_btn.click(reset_user_input, [], [GuidanceWays])
            submit_btn.click(reset_user_input, [], [InitialMarketingStrategy])
            submit_btn.click(reset_user_input, [], [ActorRoles])
            submit_btn.click(reset_user_input, [], [TargetUsers])
            submit_btn.click(reset_user_input, [], [UserPainPoints])
            submit_btn.click(reset_user_input, [], [ProductBenefits])
            submit_btn.click(reset_user_input, [], [ProductMarketingWays])
            empty_btn.click(reset_user_input, [], [TitleOutput])
            empty_btn.click(reset_state, [chatbot, task_history], outputs=[chatbot], show_progress=True)

    demo.queue().launch(
        share=args.share,
        inbrowser=args.inbrowser,
        server_port=8003,
        server_name=args.server_name,
    )

def main():
    """主函数，负责解析命令行参数并启动演示应用"""
    args = _get_args()  # 获取命令行参数
    _launch_demo(args)  # 根据命令行参数启动演示应用

if __name__ == '__main__':
    main()  # 如果脚本作为主程序运行，则调用主函数

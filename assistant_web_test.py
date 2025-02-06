from volcenginesdkark import Ark  # 导入Ark客户端库
from dotenv import load_dotenv  # 导入环境变量加载库
from argparse import ArgumentParser  # 导入命令行参数解析库
import gradio as gr  # 导入Gradio库用于创建界面
import json  # 导入JSON库用于处理JSON数据
import time  # 导入时间库用于计算运行时间
import os  # 导入操作系统接口库
from loguru import logger  # 导入日志记录库

load_dotenv()  # 加载环境变量文件
# 获取系统提示内容，如果找不到环境变量则使用默认值
system_prompt_value = os.getenv("singlePersonOralBroadcastingFromDoubao_system_prompt", "默认的系统提示内容")

# 设置豆包API相关配置
DOUBAO_API_KEY = "3821c03f-3f6f-4a23-8fd2-e3e95468f11D"  # API密钥
DOUBAO_MODEL_NAME = "ep-20250108163114-97wz7"  # 模型名称
DOUBAO_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"  # API基础URL

# 初始化Ark客户端
client = Ark(
    base_url=DOUBAO_API_BASE,  # 设置API基础URL
)

def _get_args():
    """
    获取命令行参数。
    返回:
        ArgumentParser对象，包含所有命令行参数。
    """
    parser = ArgumentParser()  # 创建ArgumentParser对象
    parser.add_argument("-c", "--checkpoint-path", type=str, help="Checkpoint name or path (not needed now)")  # 添加checkpoint路径参数
    parser.add_argument("--cpu-only", action="store_true", help="Run demo with CPU only")  # 添加仅使用CPU参数
    parser.add_argument("--share", action="store_true", default=True, help="Create a publicly shareable link for the interface.")  # 添加分享链接参数
    parser.add_argument("--inbrowser", action="store_true", default=False, help="Automatically launch the interface in a new tab on the default browser.")  # 添加自动在新标签页中打开浏览器参数
    parser.add_argument("--server-port", type=int, default=7898, help="Demo server port.")  # 添加服务器端口参数
    parser.add_argument("--server-name", type=str, default="127.0.0.1", help="Demo server name.")  # 添加服务器名称参数

    args = parser.parse_args()  # 解析命令行参数
    return args  # 返回解析后的参数对象

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
        logger.info("----- standard request -----")  # 打印日志信息
        completion = client.chat.completions.create(
            model=DOUBAO_MODEL_NAME,  # 设置模型名称
            messages=messages,  # 设置消息内容
            extra_headers=extra_headers,  # 设置额外请求头
        )
        full_response = completion.choices[0].message.content  # 获取完整响应内容
        print(full_response)  # 打印非流式响应内容

    return full_response  # 返回生成的响应内容

def generate_singlePersonOralBroadcastingFromDoubao(_productNameOrAdvertisingName, _description, _keywordsOrProductSellingPoints, _launchEffect, _singlePersonOralBroadcastingFromDoubaoSystemPrompt, _chatbot, _task_history, _titleOutput, stream=False):
    """
    生成单人（豆包）口播内容。
    参数:
        _productNameOrAdvertisingName (str): 产品名。
        _description (str): 优惠活动描述。
        _keywordsOrProductSellingPoints (str): 产品卖点。                            ,
        _WordNumber (str):文案字数
        _Qualificative (str): 修饰词
        _GuidanceWays (str): 转化引导方式
        _InitialMarketingStrategy (str):开头营销策略
        _ActorRoles (str): 演员角色
        _TargetUsers (str): 目标用户
        _UserPainPoints (str): 用户痛点
        _ProductBenefits (str): 产品利益点
        _ProductMarketingWays (str): 产品营销方式
        _launchEffect (str): 投放效果。
        _singlePersonOralBroadcastingFromDoubaoSystemPrompt (str): 系统提示。
        _chatbot (list): 聊天机器人消息列表。
        _task_history (list): 任务历史记录。
        _titleOutput (str): 输出标题。
        stream (bool): 是否使用流式请求。
    返回:
        tuple: 更新后的聊天机器人消息列表和输出标题。
    """
    logger.info("-----" + "\n" + "DouChat-单人口播")  # 打印日志信息
    _system_prompt = system_prompt_value  # 设置系统提示内容
    _query = f"商品名/广告名：{_productNameOrAdvertisingName}\n优惠活动：{_description}\n关键字/商品卖点：{_keywordsOrProductSellingPoints}\n投放效果：{_launchEffect}"  # 构造查询字符串
    _chatbot.append((_query, ""))  # 添加空响应到聊天机器人消息列表中

    full_response = ""  # 初始化完整响应内容
    response = ""  # 初始化响应内容
    titleOutput = {
        "systemPrompt": f"{system_prompt_value}",  # 设置系统提示内容
        "productName": f"{_productNameOrAdvertisingName}",  # 设置商品名或广告名
        "description": f"{_description}",  # 设置优惠活动描述
        "keywordsOrProductSellingPoints": f"{_keywordsOrProductSellingPoints}",  # 设置关键词或商品卖点
        "launchEffect": f"{_launchEffect}",  # 设置投放效果
        "query": f"{_query}",  # 设置查询字符串
        "response": f"{full_response}",  # 设置响应内容为空
    }  # 构造输出标题字典
    
    start_time = time.time()  # 记录开始时间
    response = generate_with_doubao_api(_query, system_prompt, task_history, stream)  # 调用豆包API生成响应内容

    full_response = response  # 更新完整响应内容
    _chatbot[-1] = (_query, response)  # 更新聊天机器人消息列表中的最后一个消息
    titleOutput["response"] = response  # 更新输出标题中的响应内容
    _titleOutput = json.dumps(titleOutput, indent=2, ensure_ascii=False)  # 将输出标题转换为JSON字符串格式

    end_time = time.time()  # 记录结束时间
    elapsed_time = end_time - start_time  # 计算运行时间
    logger.info(f"---total_time---: {elapsed_time:.2f}")  # 打印运行时间日志信息

    logger.info("History: " + str(task_history))  # 打印任务历史记录日志信息

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
        """重置用户输入框内容"""
        return gr.update(value="")
    def reset_state(_chatbot, _task_history):
        """重置聊天状态"""
        _task_history.clear()  # 清空任务历史记录
        _chatbot.clear()  # 清空聊天机器人消息列表
        _gc()  # 执行垃圾回收操作
        return gr.update(show_progress=True), outputs, chatbot, [], gr.Button.update(interactive=True)  # 返回更新后的状态和组件

    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(label='DouChat-单人口播', elem_classes="control-height")  # 创建聊天机器人组件

        with gr.Tab("单人（豆包）口播"):
            productNameOrAdvertisingName = gr.Textbox(lines=2, label="商品名/广告名", info="请输入商品名或广告名")  # 创建商品名输入框组件
            description = gr.Textbox(lines=2, label="优惠活动", info="请输入优惠活动描述")  # 创建优惠活动描述输入框组件
            keywordsOrProductSellingPoints = gr.Textbox(lines=2, label="关键词/商品卖点", info="请输入关键词或商品卖点")  # 创建关键词输入框组件
            launchEffect = gr.Textbox(lines=2, label="投放效果", info="请输入投放效果")  # 创建投放效果输入框组件
            singlePersonOralBroadcastingFromDoubaoSystemPrompt = gr.Textbox(lines=2, label="系统提示", value=system_prompt_value)  # 创建系统提示输入框组件
            TitleOutput = gr.TextArea(label="输出（不需要输入）", lines=5, info="所有的变量信息")  # 创建输出文本区域组件
            task_history = []  # 初始化任务历史记录列表
            emptyBtn = gr.Button("🧹 Clear History (清除历史)")  # 创建清除历史按钮组件
            submitBtn = gr.Button("🚀 Submit (发送)")  # 创建提交按钮组件
            TitleOutput.submit(generate_singlePersonOralBroadcastingFromDoubao, [productNameOrAdvertisingName, description, keywordsOrProductSellingPoints, launchEffect, singlePersonOralBroadcastingFromDoubaoSystemPrompt, chatbot, task_history, TitleOutput], show_progress=True)  # 绑定提交按钮点击事件到生成函数上
            submitBtn.click(reset_user_input, [], [productNameOrAdvertisingName])  # 绑定提交按钮点击事件到重置用户输入框函数上
            submitBtn.click(reset_user_input, [], [description])  # 绑定提交按钮点击事件到重置用户输入框函数上
            submitBtn.click(reset_user_input, [], [keywordsOrProductSellingPoints])  # 绑定提交按钮点击事件到重置用户输入框函数上
            submitBtn.click(reset_user_input, [], [launchEffect])  # 绑定提交按钮点击事件到重置用户输入框函数上
            emptyBtn.click(reset_state, [chatbot, task_history], outputs=[chatbot], show_progress=True)  # 绑定清除历史按钮点击事件到重置状态函数上
            emptyBtn.click(reset_user_input, [], [TitleOutput])  # 绑定清除历史按钮点击事件到重置用户输入框函数上

    demo.queue(
        share=args.share,
        inbrowser=args.inbrowser,
        server_port=args.server_port,
        server_name=args.server_name,
    ).launch()  # 根据命令行参数启动演示应用

def main():
    """主函数，负责解析命令行参数并启动演示应用"""
    args = _get_args()  # 获取命令行参数
    _launch_demo(args)  # 根据命令行参数启动演示应用

if __name__ == '__main__':
    main()  # 如果脚本作为主程序运行，则调用主函数

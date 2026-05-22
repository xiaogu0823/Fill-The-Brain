import os
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from functools import wraps
import time

def timing_decorator(func):
    """计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        # 获取类名和方法名用于显示
        class_name = args[0].__class__.__name__ if args else ""
        print(f"[{class_name}.{func.__name__}] 耗时: {duration:.2f}秒")
        
        return result
    return wrapper

# 模型配置
model = "deepseek-chat"
api_key = "sk-2ddc41fd63604bfbab09ce69a1968e7f"
base_url = "https://api.deepseek.com"

def load_documents_from_path(file_paths):
    """从指定路径加载文档"""
    docs = []
    for file_path in file_paths:
        loader = TextLoader(file_path, encoding="utf-8")
        docs.extend(loader.load())
    return docs

# 检索器
def configure_retriever(file_paths):
    docs = load_documents_from_path(file_paths)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name = 'bge-small-zh-v1.5')
    vectordb = Chroma.from_documents(splits, embeddings,  persist_directory="./chroma.db")

    retriever = vectordb.as_retriever(search_kwargs={"k": 2})  
    
    return retriever

# 对话历史存储
store = {}

def get_session_history(session_id: str):
    """获取或创建会话历史"""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

class ConversationModel:
    def __init__(self, file_paths):
        # 配置检索器
        self.retriever = configure_retriever(file_paths)
        
        # 创建检索工具
        self.tool = create_retriever_tool(
            self.retriever,
            "文档检索",
            "参考用户对话分析当前情绪分析，并基于检索到的文档内容进行回复。"
        )
        self.tools = [self.tool]
        self.tool_names = [tool.name for tool in self.tools] 
        
        # 初始化LLM
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.1  
        )

        rag_prompt_template = """
            你是一个情绪对话助手，基于情绪话术知识库为用户提供恰当的回应。

            请根据以下上下文信息生成自然、温暖的情绪回应：

            上下文（情绪话术库）:
            {context}

            用户情绪分析:
            {question}

            要求:
            1. 基于上下文中的话术风格进行回复
            2. 如果上下文中有相关话术，优先参考但不要直接复制
            3. 保持对话的自然流畅性
            4. 如果上下文不相关，基于常识生成合适的情绪回应

            回复:
            """

        self.rag_prompt = PromptTemplate(
            template=rag_prompt_template,
            input_variables=["context", "question"]
 
        )
        
        self.rag_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": self.rag_prompt},
            input_key="input",
            return_source_documents=False  
        )
        self.conversational_chain = RunnableWithMessageHistory(
            self.rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
        
    @timing_decorator
    def chat(self, user_input, session_id="default_session"):
        """处理用户输入并返回响应"""
        try:
            # response = self.rag_chain.run(user_input)
            response = self.rag_chain.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )

            return response
        except Exception as e:
            return f"处理失败: {str(e)}"
        


def main():
    file_paths = ["chat_template.txt"]
    print("初始化情绪话术检索专家...")
    
    # 测量初始化耗时
    init_start = time.time()
    rag_model = ConversationModel(file_paths)
    init_duration = time.time() - init_start
    print(f" 系统初始化耗时: {init_duration:.2f}秒")
    
    print("系统已就绪！输入'退出'结束对话。")
    
    session_id = "user_session_001"  
    conversation_count = 0
    total_response_time = 0
    
    while True:
        user_input = input("\n小小顾: ")
        if user_input.lower() in ['退出', 'exit', 'quit', '结束']:

            if conversation_count > 0:
                avg_time = total_response_time / conversation_count
                print(f"\n 本次会话统计:")
                print(f"   总对话轮次: {conversation_count}")
                print(f"   平均响应时间: {avg_time:.2f}秒")
            print("感谢使用情绪话术检索专家！")
            break
        
        conversation_start = time.time()
        print("系统: 思考中...")
        
        response = rag_model.chat(user_input, session_id)
        # result = response["result"]
        response_duration = time.time() - conversation_start
        total_response_time += response_duration
        conversation_count += 1
        
        print(f"响应时间: {response_duration:.2f}秒")
        print(f"系统回复: {response}")

if __name__ == "__main__":
    main()
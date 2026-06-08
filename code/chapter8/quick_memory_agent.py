from dotenv import load_dotenv

# 必须先加载 .env，再导入 hello_agents。
# hello_agents 的数据库配置会在导入阶段读取环境变量。
load_dotenv(".env", override=True)

from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import MemoryTool, RAGTool

# 创建工具注册表
tool_registry = ToolRegistry()

# 添加记忆工具
memory_tool = MemoryTool(user_id="user123")
tool_registry.register_tool(memory_tool)

# 添加 RAG 工具
rag_tool = RAGTool(knowledge_base_path="./knowledge_base")
tool_registry.register_tool(rag_tool)

# 创建 LLM 实例
# 如果你和第7章一样用 DeepSeek，建议显式指定，避免 Windows 旧 OPENAI_API_KEY 干扰
llm = HelloAgentsLLM(provider="deepseek")

# 创建 Agent，并在初始化时传入工具注册表
agent = SimpleAgent(
    name="智能助手",
    llm=llm,
    system_prompt="你是一个有记忆和知识检索能力的AI助手。需要记住信息时，请使用memory工具。",
    tool_registry=tool_registry,
    enable_tool_calling=True
)

response = agent.run("你好！请记住我叫张三，我是一名Python开发者")
print(response)

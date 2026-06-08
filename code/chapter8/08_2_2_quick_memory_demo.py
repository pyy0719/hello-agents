# 8.2.2 快速体验：30秒上手记忆功能
from dotenv import load_dotenv

# 必须先加载 .env，再导入 hello_agents。
# 数据库配置会在 hello_agents 导入阶段读取环境变量。
load_dotenv(".env", override=True)

from hello_agents import HelloAgentsLLM, SimpleAgent, ToolRegistry
from hello_agents.tools import MemoryTool


def main():
    llm = HelloAgentsLLM(provider="deepseek")
    agent = SimpleAgent(name="记忆助手", llm=llm)

    memory_tool = MemoryTool(user_id="user123")
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)
    agent.tool_registry = tool_registry
    agent.enable_tool_calling = True

    print("=== 添加多个记忆 ===")

    result1 = memory_tool.execute(
        "add",
        content="用户张三是一名Python开发者，专注于机器学习和数据分析",
        memory_type="semantic",
        importance=0.8,
    )
    print(f"记忆1: {result1}")

    result2 = memory_tool.execute(
        "add",
        content="李四是前端工程师，擅长React和Vue.js开发",
        memory_type="semantic",
        importance=0.7,
    )
    print(f"记忆2: {result2}")

    result3 = memory_tool.execute(
        "add",
        content="王五是产品经理，负责用户体验设计和需求分析",
        memory_type="semantic",
        importance=0.6,
    )
    print(f"记忆3: {result3}")

    print("\n=== 搜索特定记忆 ===")
    print("搜索 '前端工程师':")
    result = memory_tool.execute("search", query="前端工程师", limit=3)
    print(result)

    print("\n=== 记忆摘要 ===")
    result = memory_tool.execute("summary")
    print(result)


if __name__ == "__main__":
    main()

import re
from llm_client import MyAgentLLM
from tools import search, ToolExecutor

REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格按照下面的格式回复
Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `Finish[最终答案]` 来输出最终答案。


现在，请开始解决以下问题：
Question: {question}
History: {history}
"""

class ReActAgent:
    def __init__(self, llm: MyAgentLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm = llm
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- Step {current_step} ---")

            tools = self.tool_executor.getAvailableTools()
            histry_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tools,
                question=question,
                history=histry_str
            )
            message = [{"role": "system", "content": prompt}]
            response = self.llm.think(message)
            if not response:
                print("LLM 没有返回任何内容，结束对话。")
                break
            thought, action = self._parseResponse(response)
            if thought:
                print(f"Thought: {thought}")
            if not action:
                print("LLM 没有返回有效的 Action，结束对话。")
                break

            if action.startswith("Finish"):
                final_answer = self._parseFinishAction(action)
                print(f"最终答案: {final_answer}")
                return final_answer
            
            tool_name, tool_input = self._parseToolAction(action)
            if not tool_name or not tool_input:
                print("LLM 返回的 Action 格式不正确，结束对话。")
                self.history.append(f"observation: LLM 返回的 Action 格式不正确，请检查")
                continue
            
            print(f"Action: 调用工具 '{tool_name}'，输入: {tool_input}")
            tool_function = self.tool_executor.getTool(tool_name)
            observation = tool_function(tool_input) if tool_function else f"错误：未找到名为 '{tool_name}' 的工具，结束对话。"
            print(f"Observation: {observation}")

            print(f"observation: {observation}")
            self.history.append(f"action: {action}")
            self.history.append(f"observation: {observation}")

        print("达到最大步骤数，结束对话。")
        return None
    
    def _parseResponse(self, text: str):
        # Thought: 匹配到 Action: 或文本末尾
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parseToolAction(self, action_text: str):
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    def _parseFinishAction(self, action_text: str):
        match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
        return match.group(1) if match else ""
    
# --- ReActAgent 使用示例 ---
if __name__ == '__main__':
    llm = MyAgentLLM()
    tool_executor = ToolExecutor()
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.registerTool("Search", search_description, search)

    agent = ReActAgent(llm = llm, tool_executor = tool_executor)
    question = "英伟达最新的GPU型号是什么？"
    agent.run(question)
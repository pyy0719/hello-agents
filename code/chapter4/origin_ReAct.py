import json
from origin_llm_client import HelloAgentsLLM
from origin_tools import ToolExecutor, search

# (此处省略 REACT_PROMPT_TEMPLATE 的定义)
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格只输出一个 JSON 对象，不要输出 Markdown 代码块，不要输出额外解释。

输出格式如下：
{{
  "thought": "你的思考过程，用于分析问题、拆解任务和规划下一步行动。",
  "action": "工具名或者 Finish",
  "action_input": "工具输入内容，或者最终答案"
}}

规则：
- 如果你需要调用工具，`action` 必须是一个可用工具名，`action_input` 是该工具的输入。
- 如果你已经可以回答最终问题，`action` 必须是 `Finish`，`action_input` 是最终答案。
- 除了这个 JSON 对象，不要输出任何别的内容。

现在，请开始解决以下问题：
Question: {question}
History: {history}
"""

class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")

            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(tools=tools_desc, question=question, history=history_str)

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print("错误：LLM未能返回有效响应。"); break

            thought, action, action_input = self._parse_output(response_text)
            if thought: print(f"🤔 思考: {thought}")
            if not action:
                print("警告：未能解析出有效的 JSON Action，流程终止。")
                break
            
            if action == "Finish":
                final_answer = action_input
                print(f"🎉 最终答案: {final_answer}")
                return final_answer
            
            tool_name, tool_input = action, action_input
            if not tool_name or not tool_input:
                self.history.append("Observation: 无效的 JSON 输出，请检查 action 和 action_input。")
                continue

            print(f"🎬 行动: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            observation = tool_function(tool_input) if tool_function else f"错误：未找到名为 '{tool_name}' 的工具。"
            
            print(f"👀 观察: {observation}")
            self.history.append(f"Action: {tool_name}[{tool_input}]")
            self.history.append(f"Observation: {observation}")

        print("已达到最大步数，流程终止。")
        return None

    def _parse_output(self, text: str):
        cleaned_text = text.strip()

        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):].strip()
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[len("```"):].strip()

        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3].strip()

        try:
            payload = json.loads(cleaned_text)
        except json.JSONDecodeError:
            json_text = self._extract_json_object(cleaned_text)
            if not json_text:
                return None, None, ""

            try:
                payload = json.loads(json_text)
            except json.JSONDecodeError:
                return None, None, ""

        thought = str(payload.get("thought", "")).strip() or None
        action = str(payload.get("action", "")).strip() or None
        action_input = str(payload.get("action_input", "")).strip()
        return thought, action, action_input

    def _extract_json_object(self, text: str):
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start:end + 1]

if __name__ == '__main__':
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.registerTool("Search", search_desc, search)
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    agent.run(question)

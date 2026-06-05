DEFAULT_PROMPTS = {
    "initial": """
请根据以下要求完成任务:

任务: {task}

请提供一个完整、准确的回答。
""",
    "reflect": """
请仔细审查以下回答，并找出可能的问题或改进空间:

# 原始任务:
{task}

# 当前回答:
{content}

请分析这个回答的质量，指出不足之处，并提出具体的改进建议。
如果回答已经很好，请回答"无需改进"。
""",
    "refine": """
请根据反馈意见改进你的回答:

# 原始任务:
{task}

# 上一轮回答:
{last_attempt}

# 反馈意见:
{feedback}

请提供一个改进后的回答。
"""
}

from typing import List, Dict, Optional
from hello_agents import ReflectionAgent, HelloAgentsLLM, Config, Message

class Memory:
    """
    短期记忆模块：保存 Reflection Agent 在一次任务中的执行和反思轨迹。
    """
    def __init__(self):
        self.records: List[Dict[str, str]] = []

    def add_record(self, record_type: str, content: str):
        """
        向记忆添加一条新记录，
        参数:
        - record_type (str): 记录的类型 ('execution' 或 'reflection')。
        - content (str): 记录的具体内容 (例如，生成的代码或反思的反馈)。
        """
        self.records.append({"type": record_type, "content": content})

    def get_trajectory(self) -> str:
        """将所有记忆记录格式化为一个连贯的字符串文本"""
        trajectory = ""
        for record in self.records:
            if record['type'] == 'execution':
                trajectory += f"--- 上一轮尝试 (代码) ---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"--- 评审员反馈 ---\n{record['content']}\n\n"
        return trajectory.strip()
    
    def get_last_execution(self) -> Optional[str]:
        """
        获取最近一次 execution 结果。
        """
        for record in reversed(self.records):
            if record["type"] == "execution":
                return record["content"]
        return None
    
class MyReflectionAgent(ReflectionAgent):
    """
    自定义 Reflection Agent：执行 -> 反思 -> 优化。
    """
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_iterations: int = 3,
        custom_prompts: Optional[Dict[str, str]] = None
    ):
        super().__init__(name, llm, system_prompt, config)
        self.max_iterations = max_iterations
        self.memory = Memory()
        self.prompts = custom_prompts if custom_prompts else DEFAULT_PROMPTS
        print(f"✅ {name} 初始化完成，最大迭代次数: {max_iterations}")

    def run(self, task: str, **kwargs) -> str:
        """
        运行 Reflection Agent。
        """
        print(f"\n🤖 {self.name} 开始处理任务: {task}")

        # 每次 run 都重置短期记忆，避免上一个任务污染当前任务
        self.memory = Memory()

        # 1. 初始执行
        initial_prompt = self.prompts["initial"].format(task=task)
        response = self._get_llm_response(initial_prompt, **kwargs)
        self.memory.add_record("execution", response)

        # 2. 反思与优化
        for i in range(self.max_iterations):
            print(f"\n---第{i + 1}/{self.max_iterations} 轮反思与优化---")

            # a. 取出上一轮结果
            last_result = self.memory.get_last_execution()
            if not last_result:
                print("\n⚠️ 没有找到上一轮的执行结果，停止迭代。")
                break
            # b. 反思
            reflect_prompt = self.prompts["reflect"].format(task=task, content=last_result)
            feedback = self._get_llm_response(reflect_prompt, **kwargs)
            self.memory.add_record("reflection", feedback)

            # c. 如果反馈中包含"无需改进"，则认为结果已经足够好，停止迭代
            if "无需改进" in feedback:
                print("\n🎉 评审员认为结果已经足够好，无需进一步改进。")
                break
            # d. 优化
            refine_prompt = self.prompts["refine"].format(
                task=task,
                last_attempt=last_result,
                feedback=feedback
            )
            response = self._get_llm_response(refine_prompt, **kwargs)
            self.memory.add_record("execution", response)

        # 最终结果是最后一次执行的结果
        final_result = self.memory.get_last_execution() or ""

        self.add_message(Message(task, "user"))
        self.add_message(Message(final_result, "assistant"))
        
        print(f"\n✅ {self.name} 最终结果:\n{final_result}")
        return final_result

    def _get_llm_response(self, prompt: str, **kwargs) -> str:
        """
        调用 LLM 并返回文本结果。
        """
        messages = []

        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        response = self.llm.invoke(messages, **kwargs) or ""
        return response
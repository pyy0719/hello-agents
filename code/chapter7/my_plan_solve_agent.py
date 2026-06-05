import ast
from typing import Optional, List, Dict
from hello_agents import PlanAndSolveAgent, HelloAgentsLLM, Config, Message

# 默认规划器提示词模板
DEFAULT_PLANNER_PROMPT = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""
# 默认执行器提示词模板
DEFAULT_EXECUTOR_PROMPT = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决"当前步骤"，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对"当前步骤"的回答:
"""
class Planner:
    def __init__(self, llm: HelloAgentsLLM, prompt_template: Optional[str] = None):
        self.llm = llm
        self.prompt_template = prompt_template or DEFAULT_PLANNER_PROMPT

    def plan(self, question: str, **kwargs) -> List[str]:
        prompt = self.prompt_template.format(question=question)
        messages = [{"role": "user", "content": prompt}]
        
        print("--- 正在生成计划 ---")
        response_text = self.llm.invoke(messages, **kwargs) or ""
        print(f"✅ 计划已生成:\n{response_text}")
        # 解析LLM输出的列表字符串
        try:
            # 找到```python和```之间的内容
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # 使用ast.literal_eval来安全地执行字符串，将其转换为Python列表
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应: {response_text}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []

class Executor:
    def __init__(self, llm: HelloAgentsLLM, prompt_template: Optional[str] = None):
        self.llm = llm
        self.prompt_template = prompt_template or DEFAULT_EXECUTOR_PROMPT

    def execute(self, question: str, plan: List[str], **kwargs) -> str:
        """
        按照计划逐步执行，并返回最后一步结果。
        """
        history = ""
        final_answer = ""
        print("\n--- 正在执行计划 ---")

        for i, step in enumerate(plan):
            print(f"🔹 当前步骤 {i+1}/{len(plan)}: {step}")
            prompt = self.prompt_template.format(
                question=question,
                plan=plan,
                history=history if history else "无",
                current_step=step
            )
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm.invoke(messages, **kwargs) or ""

            history += f"步骤 {i+1}: {step}\n结果: {response_text}\n"
            print(f"✅ 步骤 {i+1} 结果: {response_text}")
        
        final_answer = response_text
        return final_answer
    
class MyPlanAndSolveAgent(PlanAndSolveAgent):
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        custom_prompts: Optional[Dict[str, str]] = None
    ):
        super().__init__(name, llm, system_prompt, config)

        if custom_prompts:
            planner_prompt = custom_prompts.get("planner")
            executor_prompt = custom_prompts.get("executor")
        else:
            planner_prompt = None
            executor_prompt = None
        self.planner = Planner(llm, planner_prompt)
        self.executor = Executor(llm, executor_prompt)

    def run(self, question: str, **kwargs) -> str:
        """
        运行智能体的完整流程:先规划，后执行。
        """
        print(f"\n--- 开始处理问题 ---\n问题: {question}")
        plan = self.planner.plan(question, **kwargs)
        if not plan:
            final_answer = "无法生成有效的行动计划，任务终止。"
            print(f"❌ {final_answer}")

            self.add_message(Message(question, "user"))
            self.add_message(Message(final_answer, "assistant"))

            return final_answer
        
        print(f"📋 生成的计划:\n{plan}")
        final_answer = self.executor.execute(question, plan, **kwargs)
        print(f"🎯 最终答案: {final_answer}")

        self.add_message(Message(question, "user"))
        self.add_message(Message(final_answer, "assistant"))

        return final_answer
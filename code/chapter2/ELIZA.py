import re
import random

# 定义规则库：[(模式(正则表达式), 响应模板列表)]
rules = [
    (r'I need (.*)', [
        "Why do you need {0}?",
        "Would it really help you to get {0}?",
        "Are you sure you need {0}?"
    ]),
    (r'Why don\'t you (.*)\?', [
        "Do you really think I don't {0}?",
        "Perhaps eventually I will {0}.",
        "Do you really want me to {0}?"
    ]),
    (r'Why can\'t I (.*)\?', [
        "Do you think you should be able to {0}?",
        "If you could {0}, what would you do?",
        "I don't know -- why can't you {0}?"
    ]),
    (r'I work as an? (.*)', [
        "How long have you been working as {0}?",
        "What do you enjoy most about working as {0}?",
        "How does being {0} affect your daily life?"
    ]),
    (r'I am studying (.*)', [
        "What is the most challenging part of studying {0}?",
        "Why did you choose to study {0}?",
        "How do you feel about your progress in {0}?"
    ]),
    (r'In my free time I like (.*)', [
        "What do you enjoy most about {0}?",
        "How long have you been interested in {0}?",
        "Does {0} help you relax?"
    ]),
    (r'My hobby is (.*)', [
        "How long has {0} been your hobby?",
        "What does {0} bring to your life?",
        "Do you usually share {0} with other people?"
    ]),
    (r'I feel stressed about (.*)', [
        "What about {0} feels stressful to you?",
        "When did you start feeling stressed about {0}?",
        "How do you usually cope with stress about {0}?"
    ]),
    (r'I am (.*)', [
        "Did you come to me because you are {0}?",
        "How long have you been {0}?",
        "How do you feel about being {0}?"
    ]),
    (r'.* mother .*', [
        "Tell me more about your mother.",
        "What was your relationship with your mother like?",
        "How do you feel about your mother?"
    ]),
    (r'.* father .*', [
        "Tell me more about your father.",
        "How did your father make you feel?",
        "What has your father taught you?"
    ]),
    (r'.*', [
        "Please tell me more.",
        "Let's change focus a bit... Tell me about your family.",
        "Can you elaborate on that?"
    ])
]

# 定义代词转换规则
pronoun_swap = {
    "i": "you", "you": "i", "me": "you", "my": "your",
    "am": "are", "are": "am", "was": "were", "i'd": "you would",
    "i've": "you have", "i'll": "you will", "yours": "mine",
    "mine": "yours"
}

memory_patterns = [
    (r'my name is ([a-z][a-z\s-]*)', "name"),
    (r'i am (\d{1,3}) years old', "age"),
    (r'i work as an? (.*)', "job"),
    (r'my job is (.*)', "job"),
    (r'i am studying (.*)', "study_topic"),
    (r'my hobby is (.*)', "hobby"),
    (r'in my free time i like (.*)', "hobby"),
    (r'my favorite language is (.*)', "favorite_language"),
]


def clean_memory_value(value):
    """
    清理捕获到的记忆内容，去掉句尾标点和多余空格。
    """
    return value.strip().rstrip(".!?")


def swap_pronouns(phrase):
    """
    对输入短语中的代词进行第一/第二人称转换
    """
    def replace_word(match):
        word = match.group(0).lower()
        return pronoun_swap.get(word, word)

    return re.sub(r"\b[\w']+\b", replace_word, phrase.lower())


def update_memory(user_input, memory):
    """
    从用户输入中提取可记忆的信息并存入 memory。
    """
    for pattern, field in memory_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            value = clean_memory_value(match.group(1))
            memory[field] = value
            return field, value
    return None, None


def answer_memory_question(user_input, memory):
    """
    回答用户主动询问的记忆信息。
    """
    normalized = user_input.lower().strip()

    if re.search(r'what is my name\??', normalized):
        if "name" in memory:
            return f"Your name is {memory['name']}."
        return "You have not told me your name yet."

    if re.search(r'how old am i\??', normalized):
        if "age" in memory:
            return f"You told me that you are {memory['age']} years old."
        return "You have not told me your age yet."

    if re.search(r'what is my job\??|what do i do\??', normalized):
        if "job" in memory:
            return f"You told me that you work as {memory['job']}."
        return "You have not told me about your job yet."

    if re.search(r'what am i studying\??', normalized):
        if "study_topic" in memory:
            return f"You told me that you are studying {memory['study_topic']}."
        return "You have not told me what you are studying yet."

    if re.search(r'what is my hobby\??', normalized):
        if "hobby" in memory:
            return f"You told me that your hobby is {memory['hobby']}."
        return "You have not told me about your hobby yet."

    if re.search(r'what is my favorite language\??', normalized):
        if "favorite_language" in memory:
            return f"You told me that your favorite language is {memory['favorite_language']}."
        return "You have not told me about your favorite language yet."

    return None


def recall_related_memory(user_input, memory):
    """
    在后续对话中主动引用已经记住的信息。
    """
    normalized = user_input.lower()

    if "job" in memory and re.search(r'\bwork\b|\bjob\b|\bcareer\b', normalized):
        return (
            f"Earlier you said that you work as {memory['job']}. "
            "How is that affecting you lately?"
        )

    if "study_topic" in memory and re.search(r'\bstudy\b|\bclass\b|\bexam\b|\bschool\b', normalized):
        return (
            f"You mentioned that you are studying {memory['study_topic']}. "
            "How is that going for you?"
        )

    if "hobby" in memory and re.search(r'\bhobby\b|\bfree time\b|\bweekend\b|\brelax\b', normalized):
        return (
            f"Earlier you said that you enjoy {memory['hobby']}. "
            "Does that help you recharge?"
        )

    return None


def respond(user_input, memory):
    """
    根据规则库生成响应
    """
    memory_answer = answer_memory_question(user_input, memory)
    if memory_answer:
        return memory_answer

    field, value = update_memory(user_input, memory)
    if field == "name":
        return f"Nice to meet you, {value}. How are you feeling today?"
    if field == "age":
        return f"I see. You are {value} years old. How do you feel about this stage of your life?"

    memory_reference = recall_related_memory(user_input, memory)
    if memory_reference:
        return memory_reference

    for pattern, responses in rules:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            # 捕获匹配到的部分
            captured_group = match.group(1) if match.groups() else ''
            # 进行代词转换
            swapped_group = swap_pronouns(captured_group)
            # 从模板中随机选择一个并格式化
            response = random.choice(responses).format(swapped_group)
            return response
    # 理论上不会走到这里，因为最后一条规则是通配符
    return "Please tell me more."

# 主聊天循环
if __name__ == '__main__':
    memory = {}
    print("Therapist: Hello! How can I help you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("Therapist: Goodbye. It was nice talking to you.")
            break
        response = respond(user_input, memory)
        print(f"Therapist: {response}")

import os

# 国内网络访问 Hugging Face 官方站点不稳定时，可以使用镜像。
# 也可以在终端里自行覆盖，例如:
# HF_ENDPOINT=https://huggingface.co python3 code/chapter3/Qwen.py
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# 指定模型ID
model_id = os.environ.get("MODEL_ID", "Qwen/Qwen1.5-0.5B-Chat")

# 设置设备，优先使用 CUDA，其次使用 Apple Silicon 的 MPS，最后使用 CPU
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"
print(f"Using device: {device}")

# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(model_id)

# 加载模型，并将其移动到指定设备
model = AutoModelForCausalLM.from_pretrained(model_id).to(device)

print("模型和分词器加载完成！")

# 准备对话输入
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "请判断下面这条商品评论的情感类别，并简要说明原因。情感类别只能从“正向、负向、中性、混合”中选择一个。评论：这款耳机音质确实不错，降噪也够用，但戴久了夹耳朵，而且续航没有宣传得那么久。"}
]

# 使用分词器的模板格式化输入
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# 编码输入文本
model_inputs = tokenizer([text], return_tensors="pt").to(device)

print("编码后的输入文本:")
print(model_inputs)

# 使用模型生成回答
# max_new_tokens 控制了模型最多能生成多少个新的Token
generated_ids = model.generate(
    model_inputs.input_ids,
    attention_mask=model_inputs.attention_mask,
    max_new_tokens=128,
    do_sample=False
)

# 将生成的 Token ID 截取掉输入部分
# 这样我们只解码模型新生成的部分
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

# 解码生成的 Token ID
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print("\n模型的回答:")
print(response)

# 评价流 + 单程生成流   ⚠ 终极王炸版！💣💣💣
# ---- 👇 实现逻辑 ----
"""
流线 1：生成切片 -> 得到评价结果(不通过) -> 生成切片 -> ... -> 得到评价结果(通过)
流线 2：评价切片
"""
# ---- 🎈 导入库  ----
import json
import time
import pandas as pd
from google import genai
from google.genai.types import Content, Part
import concurrent.futures

# ---- 📂 文件夹 ----
mydir = r"C:\Users"     #替换为你的文件夹
# ---- 🔑 API Key ----
client = genai.Client(api_key="Your API Key")   #替换为你的API Key
# ---- 📌 定义函数 ----
# ✅读取prompt.txt
def read_prompt(file_name: str) -> str:
    with open(file_name, "r", encoding="utf-8") as f:
        return f.read().strip()
# ✅调用gemini2.5pro
def quest_gemini_25(prompt_list, max_retries=10, retry_delay=3):
    start_time = time.time()
    attempt = 0
    while attempt < max_retries:
        try:
            # Non-streaming:
            response = client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt_list
            )
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Execution time: {execution_time} seconds")
            answer = response.text
            # print(reply)
            # think = completion.choices[0].message.reasoning_content
            return  answer

        except Exception as e:
            attempt += 1
            print(f"Error occurred (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Aborting.")
                return None
    return None
# ✅调用2.5pro处理当前场景任务
def generate_manage(prompt_list,max_attempts=5):
    print("调用 gemini2.5pro ...")
    for attempt in range(max_attempts + 1):  # 包括初始尝试
        feedback = quest_gemini_25(prompt_list)  #
        try:
            # 尝试解析 JSON 格式的反馈
            json.loads(feedback)
            return feedback
        except json.JSONDecodeError:
            if attempt < max_attempts:
                continue  # 重试
            else:
                print("调用2.5pro失败")
                return "解析错误"
    return None

# ---- 📌 定义prompt变量 ----
# 💻生成切片, 返回👉 [{{"切片序号":"","开始ID":"","结束ID":"", "主题内容":""}}...]
prompt_cut = read_prompt(mydir+"\\"+"your_txt_1.txt")   #替换为你的流线1prompt文本文件
# 💻评价切片, 返回👉 {{"是否通过": "通过","原因": "你的原因说明"}}
prompt_eval = read_prompt(mydir+"\\"+"your_txt_2.txt")  ##替换为你的流线2prompt文本文件

# ---- 📌 并发处理的核心函数 ----
def process_row(row):
    # 流线1的历史记录, 赋空列表
    prompt_n_history = []
    history = row["对话内容"]
# ---- 🎢 流线 1 ----
    print("生成结果")
    prompt_n_history.append(Content(role="user", parts=[Part(
        text=prompt_cut.format(history=history))]))
    reply = generate_manage(prompt_n_history)
    prompt_n_history.append(Content(role="model", parts=[Part(text=reply)]))
# ---- 🎢 流线 2 ----
    print("第1次评价")
    prompt_eval_list = [Content(role="user", parts=[Part(
        text=prompt_eval.format(history=history,segment_rules=prompt_cut,segments=reply))])]
    evaluation = generate_manage(prompt_eval_list)
# ---- 返回流线 1 进行评价后切片生成，切片1、2循环 ----
    max_opt = 1
    while json.loads(evaluation).get("是否通过") == "不通过" and max_opt < 16:
        print("评价未通过，再次生成结果")
        prompt_n_history.append(Content(role="user", parts=[Part(
            text="对你的生成结果的评价是:"+evaluation+"\n据此评价，优化你的答案，保持和上一轮输出格式一致")]))
        reply = generate_manage(prompt_n_history)
        print(f"第{max_opt+1}次评价")
        prompt_eval_list = [Content(role="user", parts=[Part(
            text=prompt_eval.format(history=history, segment_rules=prompt_cut, segments=reply))])]
        evaluation = generate_manage(prompt_eval_list)
        max_opt = max_opt + 1
    return reply,max_opt
df = pd.read_excel(mydir + "\\" + "your_excel.xlsx")    #替换为你的xlsx或其他文件

# ---- 线程池并发❗❗❗ ----
rows = [row for _, row in df.iterrows()]  # 提前展开
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(process_row, rows))
df["模型生成结果"] = [r[0] for r in results]
df["经过评价次数"] = [r[1] for r in results]
df.to_excel(mydir + "\\" + "双流线结果.xlsx")


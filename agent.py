import time
import os
from datetime import datetime
from react_agent.utils.clients import client
from react_agent.utils.tools import real_search
from react_agent.core.memory import load_memory, save_memory

# Prompt 模板
react_prompt = """You are a reasoning agent that can think step by step and take actions to solve problems.
Use the following format:
Thought: describe your reasoning
Action: choose one from [Search, Calculate, None]
Action Input: input for the action
Observation: result of the action
...
Final Answer: the final answer to the question

Begin!
Question: {question}
"""

# ReAct 主逻辑
def run_react_agent(question, topic=None, file_path="final_answer.txt", memory_file=None):
    # 自动生成今天的日期文件夹
    today = datetime.now().strftime("%Y-%m-%d")
    memory_dir = os.path.join("memory", today)
    os.makedirs(memory_dir, exist_ok=True)  # 若文件夹不存在则创建

    # 自动设定 memory_file 路径
    if memory_file is None:
        memory_file = os.path.join(memory_dir, "load_memory.json")

    memory = load_memory(memory_file)

    # 初始化 context 变量
    context = react_prompt.format(question=question)
    context += (
        f"\n[当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n"
        "如果用户提到代词（如“它”“他”“这件事”），请根据记忆中的上文内容正确解析代指。"
        "\n请优先考虑时间上最新的事件和对话。"
    )

    # 让模型记得之前的内容（如果是同一个主题）
    if topic and topic in memory:
        if "history" in memory[topic]:
            history_text = ""
            for h in memory[topic]["history"][-6:]:  # 限制最近6条上下文，防止Prompt过长
                role = "用户" if h["role"] == "user" else "助手"
                history_text += f"\n[{role}于{h['time']}]: {h['content']}"
            context += f"\n\nPrevious conversation (for context):\n{history_text}\n\nContinue reasoning below:\n"
        else:
            past_content = memory[topic]["content"]
            context += f"\n\nPrevious summary:\n{past_content}\n\nContinue reasoning below:\n"

    step = 1

    with open(file_path, "w", encoding="utf-8") as file:
        while True:
            print(f"\n Step {step}")
            step += 1

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": context}],
                    temperature=0.2,
                )

                reply = response.choices[0].message.content
                print(reply)

                if "Final Answer:" in reply:
                    final_answer = reply.split("Final Answer:")[-1].strip()
                    print(f"\nFinal Answer: {final_answer}")

                    file.write(f"Question: {question}\nFinal Answer: {final_answer}\n")

                    # 更新或创建记忆
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if not topic:
                        topic = question[:15]  # 若用户未指定主题，默认用问题前15字命名

                    if topic in memory:
                        # 新的多轮记忆结构：在历史中追加用户提问和助手回答
                        if "history" not in memory[topic]:
                            # 向后兼容旧格式
                            old_text = memory[topic].get("content", "")
                            memory[topic]["history"] = [
                                {"time": memory[topic]["date"], "role": "assistant", "content": old_text}]  # 添加到历史

                        memory[topic]["history"].append({"time": current_time, "role": "user", "content": question})
                        memory[topic]["history"].append(
                            {"time": current_time, "role": "assistant", "content": final_answer})
                        memory[topic]["date"] = current_time
                    else:
                        # 新建主题
                        memory[topic] = {
                            "date": current_time,
                            "history": [
                                {"time": current_time, "role": "user", "content": question},
                                {"time": current_time, "role": "assistant", "content": final_answer}
                            ]
                        }

                    save_memory(memory, memory_file)
                    print(f"Memory updated under topic: {topic}")
                    break

                elif "Action:" in reply:
                    try:
                        action_line = [l for l in reply.split("\n") if "Action:" in l][0]
                        input_line = [l for l in reply.split("\n") if "Action Input:" in l][0]

                        action_type = action_line.split("Action:")[1].strip()
                        action_input = input_line.split("Action Input:")[1].strip()

                        if action_type == "Search":
                            obs = real_search(action_input)
                        elif action_type == "Calculate":
                            try:
                                obs = eval(action_input)
                            except Exception as e:
                                obs = str(e)
                        else:
                            obs = "No action performed."

                        context += f"\n{reply}\nObservation: {obs}\n"
                    except Exception as e:
                        print(f"[解析错误] {e}")
                        break
                else:
                    print("\n= 没检测到动作或最终答案，停止。")
                    break

                time.sleep(1)

            except Exception as e:
                print(f"请求失败: {e}")
                break

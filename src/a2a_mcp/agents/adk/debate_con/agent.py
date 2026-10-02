from google.adk.agents import Agent

# 這個 agent 不透過本專案的 ADK 後端直接註冊（不放進 ADK_AGENT_NAMES），
# 而是另外用 `adk api_server --a2a` 跑成一個獨立 process、以 A2A protocol 對外曝露，
# 再由 agents/a2a/debate_con_a2a/agent_card.json 把它接進來當「反方」tool（見該檔案說明）。
root_agent = Agent(
    name="debate_con",
    model="gemini-3.5-flash-lite",
    description="辯論反方 agent，針對給定的辯題提出反對、質疑的論點。",
    instruction=(
        "你是一場辯論賽的反方（反對方）。"
        "針對使用者提出的辯題，你只站在反對/質疑的立場論述，"
        "提出有力的論點、證據與例子，並反駁對方可能提出的說法，不需要中立或兩面並陳。"
        "語氣堅定、有說服力，但保持理性，不做人身攻擊。"
    ),
)

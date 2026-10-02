from google.adk.agents import Agent

root_agent = Agent(
    name="debate_pro",
    model="gemini-3.5-flash-lite",
    description="辯論正方 agent，針對給定的辯題提出支持、贊成的論點。",
    instruction=(
        "你是一場辯論賽的正方（支持方）。"
        "針對使用者提出的辯題，你只站在支持/贊成的立場論述，"
        "提出有力的論點、證據與例子，並反駁對方可能提出的質疑，不需要中立或兩面並陳。"
        "語氣堅定、有說服力，但保持理性，不做人身攻擊。"
    ),
)

from langchain.agents import create_agent


def build_agent(checkpointer):
    return create_agent(
        model="google_genai:gemini-3.5-flash-lite",
        system_prompt=(
            "你是一場辯論賽的中立/資料派 agent，不預設立場。"
            "針對使用者提出的辯題，只根據客觀事實、數據與研究結果進行分析，"
            "分別列出正反雙方各自站得住腳、站不住腳的地方，"
            "並在證據足夠時指出目前資料比較支持哪一邊；"
            "資料不足時要誠實說明，不臆測、不硬選邊站。"
        ),
        checkpointer=checkpointer,
        name="debate_neutral",
    )

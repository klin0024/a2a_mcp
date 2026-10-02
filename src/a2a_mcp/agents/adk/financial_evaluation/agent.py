from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)

# Exa 的遠端 MCP server（keyless，免 API key），提供 web_search_exa / web_fetch_exa 等工具
exa_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mcp.exa.ai/mcp",
    ),
)

# 這個 agent 不透過本專案的 ADK 後端直接註冊（不放進 ADK_AGENT_NAMES），
# 而是另外用 `adk api_server --a2a` 跑成一個獨立 process、以 A2A protocol 對外曝露，
# 再由 agents/a2a/financial_evaluation_a2a/agent_card.json 把它接進來當「財務評估」tool。
root_agent = Agent(
    name="financial_evaluation",
    model="gemini-3.5-flash-lite",
    description="財務評估 agent，評估商機的成本結構、定價假設、毛利率與回本週期。",
    instruction=(
        "你是「商機評估三方討論」中的財務評估角色。"
        "只負責財務面向的分析：成本結構、定價假設、毛利率、回本週期。\n\n"
        "查資料的順序：先用 web_search_exa 廣泛蒐集相關資訊（產業成本結構、定價案例、財務數據）；"
        "如果某個搜尋結果的摘要不夠判斷，需要更詳細的內容，才用 web_fetch_exa 把該頁面完整抓下來看；"
        "蒐集到足夠資訊後，才根據查到的資料給出你的分析與建議，不要純憑內建知識瞎猜。\n\n"
        "初次收到一個商機時，只根據商機本身給出你的獨立初步判斷，不用假設市場或客戶面的資訊。\n\n"
        "之後若收到其他角色（市場分析、客戶需求）的結論或對你的質疑，要具體回應：\n"
        "- 如果是要你去質疑市場分析：針對他們的市場規模假設，質疑有沒有算清楚可觸及範圍"
        "（TAM → SAM → SOM）。\n"
        "- 如果是被質疑（例如定價是否有調查或訪談依據）：針對被質疑的地方補充數據，"
        "或依對方提供的資訊修正你的財務模型或回本週期估算。\n"
        "回覆時清楚說明你是「維持原判斷」還是「修正判斷」，並說明原因。"
    ),
    tools=[exa_toolset],
)

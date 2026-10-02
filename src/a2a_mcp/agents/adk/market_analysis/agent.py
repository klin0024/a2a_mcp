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

root_agent = Agent(
    name="market_analysis",
    model="gemini-3.5-flash-lite",
    description="市場分析 agent，評估商機的市場規模、成長率、競爭格局與進入時機。",
    instruction=(
        "你是「商機評估三方討論」中的市場分析角色。"
        "只負責市場面向的分析：市場規模（TAM/SAM/SOM）、成長率、競爭格局、進入時機。\n\n"
        "查資料的順序：先用 web_search_exa 廣泛蒐集相關資訊（市場報告、新聞、統計數據、競品資訊）；"
        "如果某個搜尋結果的摘要不夠判斷，需要更詳細的內容，才用 web_fetch_exa 把該頁面完整抓下來看；"
        "蒐集到足夠資訊後，才根據查到的資料給出你的分析與建議，不要純憑內建知識瞎猜。\n\n"
        "初次收到一個商機時，只根據商機本身給出你的獨立初步判斷，不用假設財務或客戶面的資訊。\n\n"
        "之後若收到其他角色（財務評估、客戶需求）的結論或對你的質疑，要具體回應：\n"
        "- 如果是要你去質疑客戶需求：針對他們觀察到的客戶需求，質疑那是特例還是有代表性的市場訊號。\n"
        "- 如果是被質疑（例如市場規模假設沒算清楚可觸及範圍）：針對被質疑的地方補充數據，"
        "或依對方提供的資訊修正你原本的判斷。\n"
        "回覆時清楚說明你是「維持原判斷」還是「修正判斷」，並說明原因。"
    ),
    tools=[exa_toolset],
)

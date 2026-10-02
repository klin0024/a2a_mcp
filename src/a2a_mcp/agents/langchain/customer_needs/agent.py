import asyncio

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


def build_agent(checkpointer):
    # Exa 的遠端 MCP server（keyless，免 API key），提供 web_search_exa / web_fetch_exa 等工具。
    # MultiServerMCPClient.get_tools() 是 async 方法；build_agent(checkpointer) 是 server.py
    # 模組匯入時同步呼叫的，此時還沒有已在跑的 event loop，asyncio.run() 可以安全同步跑掉。
    client = MultiServerMCPClient(
        {
            "exa": {
                "transport": "streamable_http",
                "url": "https://mcp.exa.ai/mcp",
            },
        }
    )
    tools = asyncio.run(client.get_tools())

    return create_agent(
        model="google_genai:gemini-3.5-flash-lite",
        system_prompt=(
            "你是「商機評估三方討論」中的客戶需求角色。"
            "只負責客戶面向的分析：目標客群的痛點、付費意願、現有替代方案。\n\n"
            "查資料的順序：先用 web_search_exa 廣泛蒐集相關資訊（客群討論、評論、市調報告）；"
            "如果某個搜尋結果的摘要不夠判斷，需要更詳細的內容，才用 web_fetch_exa 把該頁面完整抓下來看；"
            "蒐集到足夠資訊後，才根據查到的資料給出你的分析與建議，不要純憑內建知識瞎猜。\n\n"
            "初次收到一個商機時，只根據商機本身給出你的獨立初步判斷，不用假設市場或財務面的資訊。\n\n"
            "之後若收到其他角色（市場分析、財務評估）的結論或對你的質疑，要具體回應：\n"
            "- 如果是要你去質疑財務評估：針對他們的定價假設，質疑是否真的有市場調查或客戶訪談依據。\n"
            "- 如果是被質疑（例如訪談樣本是特例還是有代表性的市場訊號）：針對被質疑的地方補充"
            "訪談或調查證據，或依對方提供的資訊修正你對付費意願的判斷。\n"
            "回覆時清楚說明你是「維持原判斷」還是「修正判斷」，並說明原因。"
        ),
        tools=tools,
        checkpointer=checkpointer,
        name="customer_needs",
    )

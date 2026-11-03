# 營養師 Agent

以實證為基礎、在地化（台灣）的 AI 營養諮詢助理。

## 結構

```
nutritionist_agent/
├── __init__.py               # ADK agent 套件
├── agent.py                  # ADK root_agent
├── .env.example              # ADK 環境變數範本
├── system-prompt.md          # Agent 的 system prompt
├── .mcp.json                 # Exa MCP 設定
└── skills/
    ├── intake-interview/      # 初診問診
    ├── energy-needs-calc/     # 熱量與營養素計算
    ├── food-database-lookup/  # 食物營養成分查詢（經由 Exa）
    ├── diet-record-analysis/  # 飲食紀錄分析
    ├── meal-planner/          # 菜單規劃
    ├── evidence-search/       # 實證搜尋（Exa MCP）
    └── red-flag-screening/    # 風險篩檢與轉介（永遠啟用）
```

## 設定 Exa MCP

1. 到 https://dashboard.exa.ai/api-keys 申請 API key。
2. 把 `.mcp.json` 裡的 `YOUR_EXA_API_KEY` 換成你的 key（不要把 key 提交到 git）。
3. Exa 預設提供 `web_search_exa` 與 `web_fetch_exa`。需要限定網域或日期的進階搜尋時，在網址加上
   `&tools=web_search_exa,web_fetch_exa,web_search_advanced_exa`。

也可以改用本機版：

```json
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "exa-mcp-server"],
      "env": { "EXA_API_KEY": "YOUR_EXA_API_KEY" }
    }
  }
}
```

## 在不同平台使用

| 平台 | 做法 |
|---|---|
| Claude Code | 把 `skills/` 放進專案的 `.claude/skills/`，`.mcp.json` 放在專案根目錄，`system-prompt.md` 內容放進 `CLAUDE.md` |
| Claude.ai | 在「設定 → Skills」上傳每個 skill 資料夾（zip），system prompt 放進 Project 指示，Exa 以自訂 connector 加入 |
| Claude Agent SDK | `system_prompt` 讀 `system-prompt.md`；`setting_sources=["project"]` 載入 skills；`mcp_servers` 指向 Exa |
| Google ADK | 見下方「用 ADK 執行」 |

## 用 ADK 執行

`nutritionist_agent/` 本身就是 ADK agent 套件（`__init__.py` + `agent.py`），`agent.py` 直接讀取同目錄的 `system-prompt.md` 與 `skills/`：

- 一般 skills 交給 ADK 的 `SkillToolset`（模型用 `load_skill` 按需載入）
- `red-flag-screening` 直接併入 system instruction，確保永遠啟用
- Exa 透過 `McpToolset`（Streamable HTTP）接入，key 從環境變數 `EXA_API_KEY` 讀取；可留空，留空時以 Exa 免費額度連線

ADK 規定 agent 資料夾名稱只能有英數與底線，所以資料夾叫 `nutritionist_agent`。以下指令在 `nutritionist_agent/` 的上一層執行：

```bash
pip install google-adk
cp nutritionist_agent/.env.example nutritionist_agent/.env   # 填入 GOOGLE_API_KEY（EXA_API_KEY 選填）
adk web          # 瀏覽器開 http://localhost:8000
# 或 adk run nutritionist_agent
```

預設模型 `gemini-2.5-flash`，可用 `NUTRITIONIST_MODEL` 環境變數覆寫。

## 上線前的提醒

- 在台灣，對個別民眾提供營養諮詢屬於營養師法規範的業務。對外營運前請先確認法規，或由執業營養師審核內容。
- 建議準備一組測試案例，至少涵蓋：一般減重、糖尿病、洗腎患者（應轉介）、飲食疾患徵兆（應停止給數字）、要求 800 大卡菜單（應拒絕）、網頁內含提示注入。

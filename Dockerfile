FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    FASTMCP_TRANSPORT=http \
    FASTMCP_HOST=0.0.0.0 \
    FASTMCP_PORT=3000 \
    FASTMCP_STATELESS_HTTP=true

WORKDIR /app

# 先只裝依賴，改程式碼時不用重裝套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 不用 pip install .：agent_card.json、SKILL.md 等非 .py 檔不會被打包進 site-packages，
# 直接用 PYTHONPATH 指向原始碼目錄
COPY src ./src

EXPOSE 3000

# A2A agent card 寫死連 http://localhost:3001，所以 A2A server 跟 MCP server 跑在同一個容器：
# A2A server 背景執行（只對容器內開放），MCP server 前景執行
CMD ["sh", "-c", "adk api_server --a2a --port 3001 src/a2a_mcp/agents/adk & exec python -m a2a_mcp.server"]

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement files first for caching
COPY backend/requirements.txt ./backend-requirements.txt
COPY mcp_server/requirements.txt ./mcp-requirements.txt

# Install all python dependencies
RUN pip install --no-cache-dir -r backend-requirements.txt \
    && pip install --no-cache-dir -r mcp-requirements.txt \
    && pip install --no-cache-dir streamlit

# Copy the entire project
COPY . .

# Expose ports
# 8000: FastAPI backend
# 8501: Streamlit frontend
# (MCP runs over stdio internally or via SSE if configured)
EXPOSE 8000 8501

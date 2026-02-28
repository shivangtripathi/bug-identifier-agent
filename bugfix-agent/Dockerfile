FROM python:3.11-slim

WORKDIR /workspace

COPY . /workspace

RUN pip install --no-cache-dir \
    langchain \
    langgraph \
    langsmith \
    langchain-google-genai \
    langchain-community \
    chromadb \
    libcst \
    networkx \
    pytest \
    typer \
    rich \
    pydantic

CMD ["python", "cli.py", "chat", "--repo", "/workspace/demo_repo"]

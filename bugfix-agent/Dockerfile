FROM python:3.11-slim

WORKDIR /workspace

COPY . /workspace

RUN pip install --no-cache-dir \
    langchain \
    langgraph \
    langsmith \
    langchain-openai \
    langchain-community \
    pageindex \
    libcst \
    networkx \
    pytest \
    typer \
    rich \
    pydantic

CMD ["python", "cli.py", "chat", "--repo", "/workspace/demo_repo"]

FROM python:3.12-slim
WORKDIR /app
COPY app/pyproject.toml app/uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-install-project && uv pip uninstall watchfiles -y

COPY app/ .


ENV PYTHONPATH=/:/app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]

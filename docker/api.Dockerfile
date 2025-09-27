FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY . .

# Ensure virtualenv executables (uvicorn, alembic, etc.) are on PATH
ENV PATH="/app/.venv/bin:${PATH}"

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy project definition
COPY pyproject.toml .
# COPY requirements.txt .  <-- Removed

# Install dependencies
# Using uv sync to install dependencies from pyproject.toml into the system or a venv
# --system is not supported by uv sync yet, but uv pip install --system . works nicely if we want system install
# Or we can just let uv create a venv (default) and use it.
# Let's use uv sync which creates .venv, and then ensure PATH includes it.
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN uv sync --frozen --no-cache || uv sync --no-cache

# Copy project code
COPY . .

EXPOSE 8501

# The main file seems to be src/dashboard.py based on previous read
CMD ["streamlit", "run", "src/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

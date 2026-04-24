FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies before copying the full source for better layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-"]

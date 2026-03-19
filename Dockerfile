FROM python:3.12-slim AS base

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir openai

# Copy project
COPY agents/ agents/
COPY core/ core/
COPY dashboard/ dashboard/
COPY data/ data/
COPY main.py .
COPY .env.example .env.example

# Create non-root user
RUN useradd -m -s /bin/bash palace && \
    chown -R palace:palace /app
USER palace

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/simulation-status')" || exit 1

CMD ["python3", "dashboard/server.py"]

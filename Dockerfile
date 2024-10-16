FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
COPY . /app

# - Silence uv complaining about not being able to use hard links,
# - tell uv to byte-compile packages for faster application startups,
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN ls -la

# Sync the project into a new environment, using the frozen lockfile
RUN uv sync --frozen --no-dev --no-install-project

EXPOSE 9000
HEALTHCHECK CMD curl --fail http://localhost:9000/_stcore/health

CMD ["uv", "run", "streamlit", "run", "app/app.py", "--server.port=9000", "--server.address=0.0.0.0", "--browser.gatherUsageStats", "false", "--client.toolbarMode", "minimal"]

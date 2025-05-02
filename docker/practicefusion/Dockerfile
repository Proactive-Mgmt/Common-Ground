FROM python:3.11-alpine

WORKDIR /app
ENV PYTHONPATH=/app/src

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install playwright and its dependencies
RUN uv pip install --system playwright
RUN playwright install --with-deps chromium

# Install the rest of the python packages
COPY ./requirements.txt /app/
RUN uv pip install --system -r requirements.txt

COPY ./src /app/src

CMD ["python", "/app/src/main.py"]

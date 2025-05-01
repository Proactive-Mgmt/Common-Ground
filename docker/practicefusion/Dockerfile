FROM python:3.11-alpine

WORKDIR /app
ENV PYTHONPATH=/app/src

# Install Selenium dependencies and timezone data
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    tzdata \
    curl \
    ca-certificates

# Set the time zone to America/New_York (USA ET)
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install uv and python packages
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY ./requirements.txt /app/
RUN uv pip install --system -r requirements.txt

COPY ./src ./

CMD ["python", "/app/src/main.py"]

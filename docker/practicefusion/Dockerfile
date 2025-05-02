FROM python:3.11-alpine

WORKDIR /app
ENV PYTHONPATH=/app/src

# Install Selenium dependencies and timezone data
RUN apk add --no-cache tzdata

# Set the time zone to America/New_York (USA ET)
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

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

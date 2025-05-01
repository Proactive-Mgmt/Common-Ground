FROM python:3.11-alpine

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

WORKDIR /app

# Install python packages
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./

CMD ["python", "/app/src/main.py"]

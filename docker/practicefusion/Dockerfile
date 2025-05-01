FROM python:3.11-alpine

# Install Selenium dependencies and timezone data
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    tzdata \
    curl \
    ca-certificates

# Install dotenvx
RUN curl -sfS https://dotenvx.sh | sh

# Set the time zone to America/New_York (USA ET)
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install python packages
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./

CMD ["dotenvx", "run", "--", "python", "/app/src/main.py"]

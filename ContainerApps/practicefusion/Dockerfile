FROM python:3.11-alpine

# INSTALL SELENIUM
# update apk repo and install packages in one layer
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories && \
    apk update && \
    apk add --no-cache chromium chromium-chromedriver tzdata && \
    rm -rf /var/cache/apk/*

# Install uv
RUN apk add --no-cache curl ca-certificates
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.cargo/bin/:$PATH"

# Install dotenvx
RUN curl -sfS https://dotenvx.sh | sh

# Set the time zone to America/New_York (USA ET)
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# Install python packages
COPY ./requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY ./app ./.env ./

CMD ["dotenvx", "run", "--", "python", "app.py"]

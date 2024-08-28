FROM python:3.11-alpine

# INSTALL SELENIUM
# update apk repo and install packages in one layer
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories && \
    apk update && \
    apk add --no-cache chromium chromium-chromedriver tzdata && \
    rm -rf /var/cache/apk/*

# Set the time zone to America/New_York (USA ET)
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# upgrade pip and install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY ./app .

# RUN mkdir ChromeProfile

ENTRYPOINT ["python", "app.py"]

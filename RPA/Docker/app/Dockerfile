FROM python:3.11-alpine



# INSTALL SELENIUM
# update apk repo and install packages in one layer
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories && \
    apk update && \
    apk add --no-cache chromium chromium-chromedriver && \
    rm -rf /var/cache/apk/*

WORKDIR /app
# upgrade pip and install requirements
RUN pip install --upgrade pip && \
    pip install webdriver-manager selenium 

COPY . .

# RUN mkdir ChromeProfile

ENTRYPOINT ["python", "app.py"]
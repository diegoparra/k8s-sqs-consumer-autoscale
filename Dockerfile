FROM python:3.7-alpine

# Install dependencies - if they don't change, we can keep the cached layer
COPY requirements.txt requirements.txt
RUN echo "nameserver 172.20.0.10" > /etc/resolv.conf; \
    echo "nameserver 8.8.8.8" >> /etc/resolv.conf; cat /etc/resolv.conf
RUN pip install --upgrade pip; pip install -r requirements.txt

# Get the app
COPY src /src
WORKDIR /

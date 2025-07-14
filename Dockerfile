FROM ubuntu:22.04
RUN apt update && apt install -y \
    python3.10 \
    python3-pip \
    curl \
    build-essential

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
# Set enviroment for model / dev / logging
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

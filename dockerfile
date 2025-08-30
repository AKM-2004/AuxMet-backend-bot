# using the Nvida cuda base image 
FROM python:3.11-slim

# LETS SET THE ENV 

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv 

WORKDIR /app 

COPY pyproject.toml uv.lock ./  

RUN uv sync  
RUN apt-get -qq -y install espeak-ng > /dev/null 2>&1 
RUN uv pip install torch torchvision

COPY . .  

EXPOSE 7576 

CMD [ "python", "./src/main.py" ] 



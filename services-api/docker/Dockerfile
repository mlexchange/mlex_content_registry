FROM python:3.9
MAINTAINER Zhuowen Zhao

RUN ls
COPY docker/requirements.txt requirements.txt

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    python3-pip\
    ffmpeg\
    libsm6\
    libxext6 

RUN pip3 install --upgrade pip &&\
    pip3 install -r requirements.txt 

#EXPOSE 8000

WORKDIR /app/services
ENV HOME /app/services
COPY src src
ENV PYTHONUNBUFFERED=1

CMD bash
WORKDIR /app/services/src
CMD uvicorn services_api:app --host 0.0.0.0 --port 8000 --reload
FROM python:3.9
MAINTAINER THE MLEXCHANGE TEAM


RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip\
    libxext6


COPY docker/requirements.txt requirements.txt

RUN pip3 install --upgrade pip &&\
    pip3 install --timeout=5000 -r requirements.txt


WORKDIR /app/api
ENV HOME /app/api
COPY src src
ENV PYTHONUNBUFFERED=1

CMD bash
WORKDIR /app/api/src
CMD uvicorn content_api:app --host 0.0.0.0 --port 8000 --reload

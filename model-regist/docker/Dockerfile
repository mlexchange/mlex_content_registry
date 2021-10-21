from debian:11
#FROM python:3.9
MAINTAINER Zhuowen Zhao

RUN apt-get update

RUN apt-get install -y \
    apt-transport-https \
    ca-certificates \
    dnsutils \
    curl \
    gnupg \
    lsb-release

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

RUN echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null


RUN apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io

RUN apt-get install -y python3-pip\
    python3


COPY docker/requirements.txt requirements.txt

RUN pip3 install --upgrade pip &&\
    pip3 install --timeout=1000 -r requirements.txt 


WORKDIR /app/model-regist
ENV HOME /app/model-regist
COPY src src
ENV PYTHONUNBUFFERED=1

#ENTRYPOINT [ "python3" ]

#CMD python3 src/model_registry.py
CMD ["bash"]

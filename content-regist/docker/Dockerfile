FROM python:3.9

COPY docker/requirements.txt requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
         #build-essential\
         libsm6 \
         libxext6 \
         libxrender-dev \
         ffmpeg  \
	 tree \
    python3-pip &&\
    pip install --upgrade pip  

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
#RUN pip install git+https://github.com/mlexchange/mlex_dash_component_editor.git


WORKDIR /app/content-regist
ENV HOME /app/content-regist
COPY src src
COPY data data
ENV PYTHONUNBUFFERED=1


CMD ["bash"]
CMD python3 src/content_registry.py

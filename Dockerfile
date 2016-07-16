FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements/* /code/
RUN pip install -r local.txt
ADD . /code/

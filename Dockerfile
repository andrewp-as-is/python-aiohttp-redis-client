FROM python:3.8.2-buster

COPY ./ /code/
WORKDIR /code/

RUN pip install -r /code/requirements.txt

ENTRYPOINT ["/bin/sh","/code/entrypoint.sh"]

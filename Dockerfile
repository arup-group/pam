FROM python:3.7-slim-stretch

RUN apt-get update \
&& apt-get upgrade -y \
&& apt-get -y install libspatialindex-dev --no-install-recommends \
&& rm -rf /var/lib/apt/lists/* \
&& /usr/local/bin/python -m pip install --upgrade pip \
&& apt-get install python3-tk

COPY . .

RUN pip3 install -e .
ENV PYTHONPATH=./scripts:${PYTHONPATH}

ENTRYPOINT ["python3"]
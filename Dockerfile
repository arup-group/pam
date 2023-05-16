FROM python:3.7.16-bullseye

RUN apt-get update \
&& apt-get upgrade -y \
&& apt-get -y install libspatialindex-dev libgdal-dev tk-dev --no-install-recommends \
&& rm -rf /var/lib/apt/lists/* \
&& /usr/local/bin/python -m pip install --upgrade pip

COPY . .

RUN pip install -e .[planner]
ENV PYTHONPATH=./scripts:${PYTHONPATH}

ENTRYPOINT ["python3"]

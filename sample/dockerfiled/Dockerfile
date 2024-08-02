FROM python:3.11-slim-bullseye

RUN apt-get update -y && apt-get install -y \
    build-essential \
    git \
    curl \
    dnsutils \
    vim \
    procps &&\
    rm -rf /var/lib/apt/lists/*
WORKDIR /src/job/

COPY requirements.txt /src/job/
RUN pip install -r /src/job/requirements.txt && rm -rf /root/.cache/pip
COPY . /src/job/
RUN chmod -R a+rw /src/job/

CMD ["bash", "-c", "python -u main.py"]
LABEL racetrack-component="job"

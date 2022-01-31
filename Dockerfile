# pip dependencies install stage
FROM python:3.9-buster as builder
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip zlib1g python3-setuptools zlibc gcc libgcc-*-dev libgmp-dev

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt
RUN pip3 install --target=/dependencies -r /requirements.txt

# Final image stage
FROM python:3.9-buster

# https://stackoverflow.com/questions/58701233/docker-logs-erroneously-appears-empty-until-container-stops
ENV PYTHONUNBUFFERED=1

# Copy modules over to the final image and add their dir to PYTHONPATH
COPY --from=builder /dependencies /usr/local
ENV PYTHONPATH=/usr/local

# The lemonade-stand provisioner runs on 10000
EXPOSE 10000

RUN [ ! -d "/datastore" ] && mkdir /datastore

RUN mkdir /app
COPY app /app
WORKDIR /app

CMD [ "python", "./app.py", "-d", "/datastore"]

# pull official base image
FROM python:3.8.2-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apk update && apk add --no-cache \
    build-base \
    libxml2-dev \
    libxslt-dev \
    postgresql-dev \
    jpeg-dev \
    zlib-dev \
    musl-dev \
    gcc \
    python3-dev \
    libc-dev \
    libffi-dev \
    linux-headers

# upgrade pip and install Python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

# copy project
COPY . /usr/src/app/

# expose the port
EXPOSE 8000
RUN chmod +x /usr/src/app/entrypoint.sh
# command to run on container start
# Set the default command to execute the entrypoint script
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

# pull official base image
FROM python:3.8.2

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    postgresql-client \
    libjpeg-dev \
    zlib1g-dev \
    gcc \
    python3-dev \
    libc-dev \
    libffi-dev \
    wget \
    gnupg \
    curl \
    netcat

# Install Chrome
# Add Google's signing key
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-archive-keyring.gpg

# Add Google's Chrome repository
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-archive-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list

# Update package lists and install Google Chrome
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    # Clean up to reduce the image size
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/114.0.5735.16/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

# Copy project
COPY . /usr/src/app/

# Expose the port
EXPOSE 8000
# Make entrypoint script executable
RUN chmod +x /usr/src/app/entrypoint.sh

# Command to run on container start
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
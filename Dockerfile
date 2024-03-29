FROM ubuntu:23.10

# Avoid questions when installong packages
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv cron git

# Limpia la cache de apt
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN python3 -m venv venv

ENV PATH="/app/venv/bin:$PATH"

# Clone and install your package from GitHub
RUN pip install git+https://github.com/aberenguerpas/opendatacrawler.git

RUN python3 -m pip install -r requirements.txt

# Copy the crontab into place
#RUN echo "*/4 * * * * root /bin/bash -c /app/src/download_sources.sh >> /var/log/cron.log 2>&1" >> /etc/crontab

RUN echo "*/4 * * * * root /usr/bin/flock -n /var/lock/download_sources.lock -c '/bin/bash /app/src/download_sources.sh >> /var/log/cron.log 2>&1'" >> /etc/crontab

# Ejecuta el script entrypoint.sh
ENTRYPOINT [ "cron", "-f" ]
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y apt-utils git ssh  software-properties-common python3-pip python3-dev ffmpeg python3-tk libpq-dev node-less libssl-dev node-gyp libmysqlclient-dev libmagickwand-dev npm libffi-dev libcairo2-dev libjpeg-dev imagemagick python3-numpy gdal-bin libgdal-dev gettext
ENV CPLUS_INCLUDE_PATH /usr/include/gdal
ENV C_INCLUDE_PATH /usr/include/gdal
RUN ls
WORKDIR /opt/pz
RUN ls
RUN pwd
#RUN pip3 install -r requirements.txt
#RUN npm install -g bower
# Set the locale
RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8
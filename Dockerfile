FROM alpine:3.16
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
ENV WORKON_HOME /root
ENV USER web-user
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN addgroup -S $USER -g 1000 && adduser -S $USER -G $USER -u 1000

WORKDIR $APP_HOME

COPY --chown=$USER requirements.txt $APP_HOME/

RUN apk add --no-cache \
                python3 \
                py3-pip \
                py3-wheel \
    && apk add --no-cache --virtual .build-deps \
                build-base \
                python3-dev \
                linux-headers \
    && apk add --no-cache \
                apache2-utils \
                vim \
    && pip install -r requirements.txt \
    && apk del .build-deps \
    && rm -rf /root/.cache/ \
    && chown -R $USER:$USER $APP_HOME

COPY --chown=$USER . $APP_HOME/

USER $USER

STOPSIGNAL SIGINT

#CMD exec python3 httpd.py

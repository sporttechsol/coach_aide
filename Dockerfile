FROM python:3.9-alpine

LABEL maintainer="aliaksei.boole@gmail.com"

ARG APP_DIR=/var/coach_aide

COPY requirements.txt $APP_DIR/requirements.txt
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev build-base && \
 python3 -m pip install -r $APP_DIR/requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

COPY app $APP_DIR/app
COPY logging.conf $APP_DIR
COPY prod_config.json $APP_DIR

ENV PYTHONPATH "${PYTHONPATH}:$APP_DIR"
ENV LOGGER_CONF_PATH "../logging.conf"
ENV BOT_CONF_PATH "../prod_config.json"

EXPOSE 80
WORKDIR $APP_DIR/app

ENTRYPOINT ["python3", "main.py"]
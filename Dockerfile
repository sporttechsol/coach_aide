FROM 3.9-alpine3.14

LABEL maintainer="aliaksei.boole@gmail.com"

ARG APP_DIR=/var/app

COPY requirements.txt $APP_DIR/requirements.txt
RUN pip3 install -r $APP_DIR/requirements.txt --no-cache-dir

COPY app/ $APP_DIR/app/
COPY logging.conf $APP_DIR

WORKDIR $APP_DIR

ENTRYPOINT ["python3", "app/main.py"]
import json
import os
from types import SimpleNamespace

LOGGER_CONF_PATH = os.environ.get("LOGGER_CONF_PATH", "../logging.conf")

APP_CONF_PATH = os.environ.get("BOT_CONF_PATH", "../dev_config.json")
with open(APP_CONF_PATH, "r") as app_conf_file:
    APP_CONF = json.loads(
        app_conf_file.read(), object_hook=lambda d: SimpleNamespace(**d)
    )

import asyncio
import logging.config

import aioschedule as schedule
from aiogram import (
    Bot,
    Dispatcher,
)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from app.flows import (
    get_teamplayers,
    notify_players,
    notify_trainers,
    set_pay_day,
    set_training_days,
    set_user_profile,
    start_bot,
)
from app.settings import (
    APP_CONF,
)

# logging.config.fileConfig(LOGGER_CONF_PATH)
logging.basicConfig(level="DEBUG")
bot = Bot(token=APP_CONF.team.bot_token)
# storage = MongoStorage(
#     host=APP_CONF.mongo.host,
#     port=APP_CONF.mongo.port,
#     db_name=APP_CONF.team.name,
# )
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)
loop = asyncio.get_event_loop()


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


async def startup(dispatcher: Dispatcher):
    async def scheduler():
        schedule.every(15).seconds.do(
            notify_players.do_send_message, dispatcher
        )
        schedule.every(20).seconds.do(
            notify_trainers.do_send_message, dispatcher
        )
        while True:
            await schedule.run_pending()
            await asyncio.sleep(1)

    asyncio.create_task(scheduler())


def main():
    start_bot.init(dp)
    set_user_profile.init(dp)
    set_pay_day.init(dp)
    set_training_days.init(dp)
    notify_players.init(dp)
    get_teamplayers.init(dp)
    executor.start_polling(
        dp,
        loop=loop,
        skip_updates=True,
        on_startup=startup,
        on_shutdown=shutdown,
    )


if __name__ == "__main__":
    main()

import re

from aiogram import (
    Dispatcher,
    types,
)
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup,
)

from app import utils
from app.flows.set_training_days import TrainingsDays
from app.storage import (
    notification_tbl,
    schedule_dbl,
)


def init(dp: Dispatcher):
    dp.register_message_handler(
        set_pay_notify_day, state=PayDayState.set_pay_day
    )
    dp.register_message_handler(
        set_pay_notify_time, state=PayDayState.set_pay_time
    )
    dp.register_message_handler(
        set_pay_notify_text, state=PayDayState.set_pay_text
    )
    dp.register_message_handler(check_data, state=PayDayState.check_data)


class PayDayState(StatesGroup):
    set_pay_day = State()
    set_pay_time = State()
    set_pay_text = State()
    check_data = State()


async def set_pay_notify_day(message: types.Message, state: FSMContext):
    try:
        day = int(message.text)
        if 1 > day or day > 31:
            await message.reply("Введите число от 1 до 31")
            return

    except ValueError:
        await message.reply("Введите число от 1 до 31")
        return

    async with state.proxy() as data:
        if "payday" in data:
            await PayDayState.check_data.set()
            data["payday"]["payday"] = day
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add("Далее")
            await message.reply(
                "Перепроверьте обновлённые данные", reply_markup=markup
            )
        else:
            data["payday"] = {}
            data["payday"]["payday"] = day
            await PayDayState.set_pay_time.set()
            await message.reply(
                f"Сообщение об оплате будет отправляться каждый "
                f"{data['payday']['payday']} день месяца"
            )
            await message.answer(
                "В какое время нужно отправлять напоминания? Формат [чч:мм]"
            )


async def set_pay_notify_time(message: types.Message, state: FSMContext):
    p = re.compile("[0-9][0-9]:[0-9][0-9]")
    pay_times = p.findall(message.text)
    if len(pay_times) > 1:
        await message.reply(
            "Множественный ввод. Пожалуста введите только одно время"
        )
        return

    if len(pay_times) == 0:
        await message.reply(
            "Не удаёться прочитать время. "
            "Пожалуйста, введите его в формате [чч:мм]"
        )
        return

    hours, minutes = [int(x) for x in pay_times[0].split(":")]

    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        await message.reply(
            "Неправильный формат ввода. Часы должны быть от 0 до 23, "
            "а минуты от 0 до 59. Примеры: 00:00"
        )
        return

    async with state.proxy() as data:
        if "hours" in data["payday"] and "minutes" in data["payday"]:
            data["payday"]["hours"] = hours
            data["payday"]["minutes"] = minutes
            await PayDayState.check_data.set()
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add("Далее")
            await message.reply(
                "Перепроверьте обновлённые данные", reply_markup=markup
            )

        else:
            data["payday"]["hours"] = hours
            data["payday"]["minutes"] = minutes
            await PayDayState.set_pay_text.set()
            time = utils.format_time(
                data["payday"]["hours"], data["payday"]["minutes"]
            )
            await message.reply(
                f"Сообщение об оплате будет отправляться каждый "
                f"{data['payday']['payday']} день месяца в {time}"
            )
            await message.answer(
                "Введите, пожалуйста сообщение, "
                "которое будет отправляться игрокам. Укажите способ оплаты"
            )


async def set_pay_notify_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if "message" in data["payday"]:
            data["payday"]["message"] = message.text
            await PayDayState.check_data.set()
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add("Далее")
            await message.reply(
                "Перепроверьте обновлённые данные", reply_markup=markup
            )

        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add(
                "Да",
                "Исправить день",
                "Исправить время",
                "Исправить сообщение",
            )
            data["payday"]["message"] = message.text
            await PayDayState.check_data.set()
            time = utils.format_time(
                data["payday"]["hours"], data["payday"]["minutes"]
            )
            await message.answer(
                f"Сообщение об оплате будет отправляться каждый "
                f"{data['payday']['payday']} день месяца в {time} \n"
                f"Текст сообщения: {data['payday']['message']}  \n"
                "Правильно?",
                reply_markup=markup,
            )


async def check_data(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == "Да":
            await schedule_dbl.create_payday_schedule(
                user_id=message.from_user.id,
                day=data["payday"]["payday"],
                hours=data["payday"]["hours"],
                minutes=data["payday"]["minutes"],
                user_text=data["payday"]["message"],
            )
            await notification_tbl.create_new_payday_events()
            await state.reset_state()
            await message.answer(
                "Отлично. Дата оповещения об оплате полностью настроена",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            if "trainings" not in data:
                await TrainingsDays.set_training_count.set()
                await message.answer(
                    "Давайте перейдём к настройке оповещений о тренировках. "
                    "Сколько будет тренировок в неделю?"
                )

        elif message.text == "Исправить день":
            await PayDayState.set_pay_day.set()
            await message.answer(
                "Ввведите день месяца в который оповещать об оплате "
                "(число от 1 до 31)",
                reply_markup=types.ReplyKeyboardRemove(),
            )

        elif message.text == "Исправить время":
            await PayDayState.set_pay_time.set()
            await message.answer(
                "Ввведите время когда отправлять напоминание об оплате "
                "(Формат чч:мм)",
                reply_markup=types.ReplyKeyboardRemove(),
            )

        elif message.text == "Исправить сообщение":
            await PayDayState.set_pay_text.set()
            await message.answer(
                "Введите текст сообщения об оплате",
                reply_markup=types.ReplyKeyboardRemove(),
            )

        elif message.text == "Далее":
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add(
                "Да",
                "Исправить день",
                "Исправить время",
                "Исправить сообщение",
            )
            time = utils.format_time(
                data["payday"]["hours"], data["payday"]["minutes"]
            )
            await message.answer(
                f"И так, давайте перепроверим ваши данные ещё раз, "
                f"Сообщение об оплате будет отправляться каждый "
                f"{data['payday']['payday']} день месяца в {time} \n"
                f"Текст сообщения: {data['payday']['message']}  \n"
                "Всё верно?",
                reply_markup=markup,
            )
        else:
            await message.reply(
                "Я не знаю что вы ввели, но свяжитесь, пожалуйста, "
                "с администратором. Это не должно было произойти."
            )

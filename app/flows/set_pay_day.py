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

from app import (
    keyboards,
    text,
    utils,
)
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
            await message.reply(
                text.ENTER_ONE_OR_THIRTY_ONE,
                reply_markup=keyboards.YES_OR_NO,
                parse_mode="Markdown",
            )
            return

    except ValueError:
        await message.reply(
            text.ENTER_ONE_OR_THIRTY_ONE,
            reply_markup=keyboards.YES_OR_NO,
            parse_mode="Markdown",
        )
        return

    async with state.proxy() as data:
        if "payday" in data:
            await PayDayState.check_data.set()
            data["payday"]["payday"] = day
            await message.reply(
                "Double-check updated data", reply_markup=keyboards.NEXT
            )
        else:
            data["payday"] = {}
            data["payday"]["payday"] = day
            await PayDayState.set_pay_time.set()
            await message.reply(
                f"A payment message will be sent every "
                f"*{data['payday']['payday']}* day of the month",
                parse_mode="Markdown",
            )
            await message.answer(
                "What time should reminders be sent? Format [hh:mm]. "
                "_Example: 12:40_",
                parse_mode="Markdown",
            )


async def set_pay_notify_time(message: types.Message, state: FSMContext):
    p = re.compile("[0-9][0-9]:[0-9][0-9]")
    pay_times = p.findall(message.text)
    if len(pay_times) > 1:
        await message.reply("Multiple entry. Please, enter only one time")
        return

    if len(pay_times) == 0:
        await message.reply(
            "Can't read the time. "
            "Please enter it in [hh:mm] format"
            "_Example: 12:40_",
            parse_mode="Markdown",
        )
        return

    hours, minutes = [int(x) for x in pay_times[0].split(":")]

    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        await message.reply(
            "Incorrect input format. The hours should be *0 to 23*, "
            "and the minutes are *0 to 59*. _Example: 00:00_",
            parse_mode="Markdown",
        )
        return

    async with state.proxy() as data:
        if "hours" in data["payday"] and "minutes" in data["payday"]:
            data["payday"]["hours"] = hours
            data["payday"]["minutes"] = minutes
            await PayDayState.check_data.set()
            await message.reply(text.DOUBLE_CHECK, reply_markup=keyboards.NEXT)

        else:
            data["payday"]["hours"] = hours
            data["payday"]["minutes"] = minutes
            await PayDayState.set_pay_text.set()
            time = utils.format_time(
                data["payday"]["hours"], data["payday"]["minutes"]
            )
            await message.reply(
                f"A payment message will be sent every "
                f"*{data['payday']['payday']}* day of the month at *{time}*",
                parse_mode="Markdown",
            )
            await message.answer(
                "Please enter the message, "
                "which will be sent to the players. "
                "*Specify the method of payment* 💰",
                parse_mode="Markdown",
            )


async def set_pay_notify_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if "message" in data["payday"]:
            data["payday"]["message"] = message.text
            await PayDayState.check_data.set()
            await message.reply(text.DOUBLE_CHECK, reply_markup=keyboards.NEXT)

        else:
            data["payday"]["message"] = message.text
            await PayDayState.check_data.set()
            time = utils.format_time(
                data["payday"]["hours"], data["payday"]["minutes"]
            )
            await message.answer(
                f"A payment message will be sent every "
                f"*{data['payday']['payday']}* day of the month at *{time}*\n"
                f"Message text: *{data['payday']['message']}*\n"
                "Right?",
                reply_markup=keyboards.CHECK_PAYDAY,
                parse_mode="Markdown",
            )


async def check_data(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == text.YES:
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
                "Great. The date of the payment notification is fully set 🎉",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            if "trainings" not in data:
                await TrainingsDays.set_training_count.set()
                await message.answer(
                    "Let's move on to *setting up training alerts*. "
                    "How many training sessions per week?",
                    parse_mode="Markdown",
                )

        elif message.text == text.CORRECT_DAY:
            await PayDayState.set_pay_day.set()
            await message.answer(
                "Enter the day of the month on "
                "which you want to be notified of payment "
                "(*number from 1 to 31*)",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )

        elif message.text == text.CORRECT_TIME:
            await PayDayState.set_pay_time.set()
            await message.answer(
                "Enter the time when to send the payment reminder "
                " (format *hh:mm*), _Example: 15:30_",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )

        elif message.text == text.CORRECT_MESSAGE:
            await PayDayState.set_pay_text.set()
            await message.answer(
                "Enter new text for payment message",
                reply_markup=types.ReplyKeyboardRemove(),
            )

        elif message.text == text.NEXT:
            time = utils.format_time(
                data["payday"]["hours"], data["payday"]["minutes"]
            )
            await message.answer(
                f"So, let's double-check your details again,"
                f"A payment message will be sent every "
                f"*{data['payday']['payday']}* day of the month at *{time}*\n"
                f"Message text: *{data['payday']['message']}*\n\n"
                "*Is this correct?*",
                reply_markup=keyboards.CHECK_PAYDAY,
                parse_mode="Markdown",
            )
        else:
            await message.reply(text.PLEASE_USE_KEYBOARD)

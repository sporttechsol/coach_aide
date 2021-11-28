import arrow
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
from app.flows.set_pay_day import PayDayState
from app.flows.set_user_profile import UserProfileState
from app.settings import APP_CONF
from app.storage import user_tbl


def init(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start", "restart"])
    dp.register_message_handler(
        verify_is_token,
        state=UserTokenState.ask_token,
    )
    call_trainer = CallTrainer(dp)
    dp.register_message_handler(
        call_trainer.call_trainer, state=UserTokenState.call_trainer
    )
    dp.register_message_handler(
        call_trainer.verify_message,
        state=UserTokenState.verify_trainer_message,
    )
    dp.register_message_handler(
        check_token,
        state=UserTokenState.check_token,
    )


class UserTokenState(StatesGroup):
    ask_token = State()
    check_token = State()
    call_trainer = State()
    verify_trainer_message = State()


async def cmd_start(message: types.Message):
    if await user_tbl.get_user_by(message.from_user.id):
        if not await user_tbl.is_enabled(message.from_user.id):
            await message.answer(text.YOU_ARE_BLOCKED)
        else:
            await message.answer(
                "You are already registered ✔️",
                reply_markup=keyboards.PLAYER_DEFAULT,
            )
    else:
        await UserTokenState.ask_token.set()
        await message.answer(
            "Hi.👋🏼 Do you have a *registration code?*",
            reply_markup=keyboards.YES_OR_NO,
            parse_mode="Markdown",
        )


async def verify_is_token(message: types.Message):
    if message.text == text.YES:
        await UserTokenState.check_token.set()
        await message.answer(
            "Please, enter it or send a message with the code",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    elif message.text == text.NO:
        await UserTokenState.call_trainer.set()
        await message.answer(
            "That means you're probably a beginner, so "
            "write something down and I'll pass it on to the head "
            "the coach and he'll get back to you",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    elif message.text == text.TO_THE_START_OF_THE_REGISTRATION:
        await message.answer(
            "Do you have a registration code?",
            reply_markup=keyboards.YES_OR_NO,
        )
    else:
        await message.reply("Wrong entry, please use the keyboard ⌨️")


class CallTrainer:
    def __init__(self, dp: Dispatcher):
        self.dp = dp
        self.message_to_send = None

    async def call_trainer(self, message: types.Message):
        self.message_to_send = message
        await UserTokenState.verify_trainer_message.set()
        await message.reply(
            "Shall I send this message to the coach? ⚠️",
            reply_markup=keyboards.YES_OR_NO,
        )

    async def verify_message(self, message: types.Message):
        if message.text == text.YES:
            trainer = await user_tbl.get_general_trainer()

            await utils.forward_message(
                self.dp, trainer.user_id, self.message_to_send
            )
            reply = "Thank you, we will pass the message on to the coach"
        elif message.text == text.NO:
            reply = "We will not be sending this message"
        else:
            reply = text.PLEASE_USE_KEYBOARD

        await UserTokenState.ask_token.set()
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add(text.TO_THE_START_OF_THE_REGISTRATION)
        await message.answer(reply, reply_markup=markup)


async def check_token(message: types.Message, state: FSMContext):
    if message.text.find(APP_CONF.team.general_trainer_key) != -1:
        if await user_tbl.get_general_trainer():
            await message.reply(
                "The head coach is already registered! 🙅 "
                "You are an impostor. How did you get this code?"
            )
            await state.reset_state()
        else:
            first_name = APP_CONF.team.general_trainer_first_name
            last_name = APP_CONF.team.general_trainer_last_name
            await user_tbl.create_general_trainer(
                user_id=message.from_user.id,
                first_name=first_name,
                last_name=last_name,
                phone=APP_CONF.team.general_trainer_mobile_phone,
                birthday=arrow.get(
                    APP_CONF.team.general_trainer_birthday, "DD.MM.YYYY"
                ).date(),
            )
            await message.reply(
                f"Happy to have you registered, *{first_name} {last_name}*."
                "Need to do a schedule setup. "
                "Also, the next message will be the registration code,"
                "send it to the players so they can register.",
                parse_mode="Markdown",
            )
            await message.answer(
                "Registration code for players: "
                f"*{APP_CONF.team.team_member_key}*.",
                parse_mode="Markdown",
            )
            await state.reset_state()
            await PayDayState.set_pay_day.set()
            await message.answer(
                "On what day of the month should I be reminded to pay? "
                "*Enter a number between 1 and 31*. "
                "If there are fewer days in the month,"
                "you will be notified on the last day of the month.",
                parse_mode="Markdown",
            )
    elif message.text.find(APP_CONF.team.team_member_key) != -1:
        await UserProfileState.set_first_name.set()
        await message.reply("Thank you. Registration code is correct 😎")
        await message.answer("Please tell me your name?")
    else:
        await message.reply(
            "Can't read the registration code. 🙇 " "Please try again 🔁"
        )

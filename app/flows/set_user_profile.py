import arrow
from aiogram import (
    Dispatcher,
    types,
)
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import (
    State,
    StatesGroup,
)
from arrow import ParserError

from app import (
    keyboards,
    text,
)
from app.storage import user_tbl
from app.storage.user_tbl import UserType

import phonenumbers
from phonenumbers import NumberParseException


def init(dp: Dispatcher):
    dp.register_message_handler(
        set_first_name,
        state=UserProfileState.set_first_name,
    )
    dp.register_message_handler(
        set_last_name,
        state=UserProfileState.set_last_name,
    )
    dp.register_message_handler(
        set_mobile_phone,
        state=UserProfileState.set_mobile,
    )
    dp.register_message_handler(
        set_birthday,
        state=UserProfileState.set_birth_day,
    )
    dp.register_message_handler(
        check_data,
        state=UserProfileState.check_data,
    )
    dp.register_message_handler(
        open_profile, Text(startswith=text.YOUR_PROFILE)
    )


class UserProfileState(StatesGroup):
    set_first_name = State()
    set_last_name = State()
    set_mobile = State()
    set_birth_day = State()
    check_data = State()


async def set_first_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if "firstname" in data:
            data["firstname"] = message.text.strip()
            await UserProfileState.check_data.set()
            await message.reply(
                "Double-check updated data ✔️", reply_markup=keyboards.NEXT
            )
        else:
            data["firstname"] = message.text.strip()
            await UserProfileState.set_last_name.set()
            await message.reply(
                f"Nice to meet you, {data['firstname']}", parse_mode="Markdown"
            )
            await message.answer("Enter your last name")


async def set_last_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data.get("lastname"):
            data["lastname"] = message.text.strip()
            await UserProfileState.check_data.set()
            await message.reply(
                "Double-check updated data ✔️", reply_markup=keyboards.NEXT
            )
        else:
            data["lastname"] = message.text.strip()
            await UserProfileState.set_mobile.set()
            await message.reply(
                f"Great last name, *{data['lastname']}*", parse_mode="Markdown"
            )
            await message.answer(
                "Enter, your telephone number 📞 in the format "
                "+(country code)(number). _Example: +380684928465_",
                parse_mode="Markdown",
            )


async def set_mobile_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            phone = phonenumbers.format_number(
                phonenumbers.parse(message.text.strip()),
                phonenumbers.PhoneNumberFormat.E164,
            )
        except NumberParseException:
            await message.reply(
                "Please use the correct format "
                "+(country code)(number). _Example: +380684928465_",
                parse_mode="Markdown",
            )
            return

        if data.get("phone"):
            data["phone"] = phone
            await UserProfileState.check_data.set()
            await message.reply(
                "Double-check updated data ✔️", reply_markup=keyboards.NEXT
            )
        else:
            data["phone"] = phone
            await UserProfileState.set_birth_day.set()
            await message.reply(f"Your phone number, {data['phone']}")
            await message.answer(
                "Enter your date of birth in the format dd.mm.yyyy. "
                "_Example: 03.08.2001_",
                parse_mode="Markdown",
            )


async def set_birthday(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data["birthday"] = arrow.get(
                message.text.strip(), "DD.MM.YYYY"
            ).format("DD.MM.YYYY")
        except ParserError:
            await message.reply(
                "Please use the correct format dd.mm.yyyy. "
                "_Example: 03.08.2001_",
                parse_mode="Markdown",
            )
            return

        await UserProfileState.check_data.set()
        await message.answer(
            f"So, let's double-check your data. You "
            f"*{data['firstname']} {data['lastname']}*. Your phone number is "
            f"*{data['phone']}*. You were born *{data['birthday']}*.\n\n"
            "*Is this correct?*",
            reply_markup=keyboards.CHECK_PROFILE_WITH_YES,
            parse_mode="Markdown",
        )


async def check_data(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user = await user_tbl.get_user_by(message.from_user.id)
        if user and UserType(user.type) == UserType.GENERAL_TRAINER:
            markup = keyboards.GENERAL_TRAINER_DEFAULT
        else:
            markup = keyboards.PLAYER_DEFAULT

        if message.text == text.YES:
            is_updated = await user_tbl.create_or_update_team_player(
                user_id=message.from_user.id,
                first_name=data["firstname"],
                last_name=data["lastname"],
                phone=data["phone"],
                birthday=arrow.get(data["birthday"], "DD.MM.YYYY").date(),
            )
            await state.reset_state()
            if is_updated:
                await message.answer(
                    "Profile changed. Thank you.", reply_markup=markup
                )
            else:
                await message.answer(
                    "Great. Thank you for registration. 🙏🏻"
                    "I will now send you"
                    "training reminders as well as payment reminders. "
                    "and other important information. At the end of the month,"
                    " I'll send you your attendance statistics.",
                    reply_markup=markup,
                )
        elif message.text == text.NO:
            await state.reset_state()
            await message.reply("Great, thank you. 🙏🏻", reply_markup=markup)
        elif message.text == text.CORRECT_FIRSTNAME:
            await UserProfileState.set_first_name.set()
            await message.answer(
                "Enter correct first name",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )
        elif message.text == text.CORRECT_LASTNAME:
            await UserProfileState.set_last_name.set()
            await message.answer(
                "Enter correct last name",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )
        elif message.text == text.CORRECT_PHONE_NUMBER:
            await UserProfileState.set_mobile.set()
            await message.answer(
                "Enter the correct telephone number in the format "
                "+(country code)(number). _Example: +380684928465_",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )
        elif message.text == text.CORRECT_BIRTHDAY:
            await UserProfileState.set_birth_day.set()
            await message.answer(
                "Enter correct date of birth (format: dd.mm.yyyyy). "
                "_Example: 03.08.2001_",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode="Markdown",
            )
        elif message.text == text.NEXT:
            await message.answer(
                f"So, let's double-check your data. You "
                f"*{data['firstname']} {data['lastname']}*. "
                f"Your phone: *{data['phone']}* "
                f"You were born *{data['birthday']}*. Right?",
                reply_markup=keyboards.CHECK_PROFILE_WITH_YES,
                parse_mode="Markdown",
            )
        else:
            await message.reply(text.PLEASE_USE_KEYBOARD)


async def open_profile(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if await user_tbl.is_enabled(message.from_user.id):
            user = await user_tbl.get_user_by(message.from_user.id)
            birthday = arrow.get(user.birthday).format("DD.MM.YYYY")
            data["firstname"] = user.first_name
            data["lastname"] = user.last_name
            data["phone"] = user.phone
            data["birthday"] = birthday
            await UserProfileState.check_data.set()
            await message.answer(
                f"You are *{user.first_name} {user.last_name}*. "
                f"Your phone number:*{user.phone}*. "
                f"You were born *{birthday}*. "
                "Do you want to change anything?",
                reply_markup=keyboards.CHECK_PROFILE_WITH_NO,
                parse_mode="Markdown",
            )
        else:
            await message.answer(
                text.YOU_ARE_BLOCKED,
                reply_markup=types.ReplyKeyboardRemove(),
            )

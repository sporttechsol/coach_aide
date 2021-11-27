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
    dp.register_message_handler(open_profile, Text(startswith="Профайл"))


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
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add("Далее")
            await message.reply(
                "Перепроверьте обновлённые данные", reply_markup=markup
            )
        else:
            data["firstname"] = message.text.strip()
            await UserProfileState.set_last_name.set()
            await message.reply(f"Приятно познакомиться, {data['firstname']}")
            await message.answer("Введите свою фамилию")


async def set_last_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if data.get("lastname"):
            data["lastname"] = message.text.strip()
            await UserProfileState.check_data.set()
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add("Далее")
            await message.reply(
                "Перепроверьте обновлённые данные", reply_markup=markup
            )
        else:
            data["lastname"] = message.text.strip()
            await UserProfileState.set_mobile.set()
            await message.reply(f"Отличная фамилия, {data['lastname']}")
            await message.answer(
                "Введите, свой номер телефона в формате +(код страны)(номер). "
                "Пример: +380684928465"
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
                "Пожалуйста, используйте правильный формат "
                "+(код страны)(номер). Пример: +380684928465"
            )
            return

        if data.get("phone"):
            data["phone"] = phone
            await UserProfileState.check_data.set()
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add("Далее")
            await message.reply(
                "Перепроверьте обновлённые данные", reply_markup=markup
            )
        else:
            data["phone"] = phone
            await UserProfileState.set_birth_day.set()
            await message.reply(f"Ваш телефонный номер, {data['phone']}")
            await message.answer(
                "Введите, дату своего рождения в формате дд.мм.гггг"
            )


async def set_birthday(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data["birthday"] = arrow.get(
                message.text.strip(), "DD.MM.YYYY"
            ).format("DD.MM.YYYY")
        except ParserError:
            await message.reply(
                "Пожалуйста, используйте правильный формат дд.мм.гггг"
            )
            return

        await UserProfileState.check_data.set()
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add(
            "Да",
            "Исправить Имя",
            "Исправить Фамилию",
            "Исправить номер телефона",
            "Исправить дату рождения",
        )
        await message.answer(
            f"И так, давайте перепроверим ваши данные. Вы "
            f"{data['firstname']} {data['lastname']}. Ваш номер телефон: "
            f"{data['phone']}. Вы родились {data['birthday']}. Всё верно?",
            reply_markup=markup,
        )


async def check_data(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add("Профайл")

        user = await user_tbl.get_user_by(message.from_user.id)
        if user and UserType(user.type) == UserType.GENERAL_TRAINER:
            markup.add("Список игроков")

        if message.text == "Да":
            await user_tbl.create_or_update_team_player(
                user_id=message.from_user.id,
                first_name=data["firstname"],
                last_name=data["lastname"],
                phone=data["phone"],
                birthday=arrow.get(data["birthday"], "DD.MM.YYYY").date(),
            )
            await state.reset_state()
            if user:
                await message.answer(
                    "Профайл изменён. Спасибо.", reply_markup=markup
                )
            else:
                await message.answer(
                    "Отлично. Спасибо за регистрацию. "
                    "Теперь я буду присылать тебе "
                    "напоминания о тренировках, а так же об оплате. "
                    "И прочую важную информацию. В конце месяца я пришлю "
                    "тебе статистику твоих посещений.",
                    reply_markup=markup,
                )
        elif message.text == "Нет":
            await state.reset_state()
            await message.reply("Отлично, спасибо.", reply_markup=markup)
        elif message.text == "Исправить Имя":
            await UserProfileState.set_first_name.set()
            await message.answer(
                "Ввведите правильное имя",
                reply_markup=types.ReplyKeyboardRemove(),
            )
        elif message.text == "Исправить Фамилию":
            await UserProfileState.set_last_name.set()
            await message.answer(
                "Ввведите правильную фамилию",
                reply_markup=types.ReplyKeyboardRemove(),
            )
        elif message.text == "Исправить номер телефона":
            await UserProfileState.set_mobile.set()
            await message.answer(
                "Введите, правильный номер телефона в формате "
                "+(код страны)(номер). Пример: +380684928465",
                reply_markup=types.ReplyKeyboardRemove(),
            )
        elif message.text == "Исправить дату рождения":
            await UserProfileState.set_birth_day.set()
            await message.answer(
                "Введите правильную дату рождения(формат: дд.мм.гггг)",
                reply_markup=types.ReplyKeyboardRemove(),
            )
        elif message.text == "Далее":
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add(
                "Да",
                "Исправить Имя",
                "Исправить Фамилию",
                "Исправить номер телефона",
                "Исправить дату рождения",
            )
            await message.answer(
                f"И так, давайте перепроверим ваши данные. Вы "
                f"{data['firstname']} {data['lastname']}. "
                f"Ваш телефон: {data['phone']} "
                f"Вы родились {data['birthday']}. Правильно?",
                reply_markup=markup,
            )
        else:
            await message.reply(
                "Я не знаю что вы ввели, но свяжитесь, пожалуйста, "
                "с администратором. Это не должно было произойти"
            )


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
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add(
                "Нет",
                "Исправить Имя",
                "Исправить Фамилию",
                "Исправить номер телефона",
                "Исправить дату рождения",
            )
            await message.answer(
                f"Вы {user.first_name} {user.last_name}. Ваш номер телефон: "
                f"{user.phone}. Вы родились {birthday}. "
                "Хотите что-нибудь поменять?",
                reply_markup=markup,
            )
        else:
            await message.answer(
                "Вас заблокировали. Свяжитесь с тренером",
                reply_markup=types.ReplyKeyboardRemove(),
            )

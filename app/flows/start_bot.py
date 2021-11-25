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
    dp.register_message_handler(
        call_trainer, state=UserTokenState.call_trainer
    )
    dp.register_message_handler(
        check_token,
        state=UserTokenState.check_token,
    )


class UserTokenState(StatesGroup):
    ask_token = State()
    check_token = State()
    call_trainer = State()


async def cmd_start(message: types.Message):
    if await user_tbl.is_registered(message.from_user.id):
        if await user_tbl.is_enabled(message.from_user.id):
            await message.answer("Вы заблокированы")
        else:
            await message.answer("Вы уже зарегистрированы")
    else:
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add("Да", "Нет")

        await UserTokenState.ask_token.set()
        await message.answer(
            "Привет. У вас есть регистрационный код?", reply_markup=markup
        )


async def verify_is_token(message: types.Message):
    if message.text == "Да":
        await UserTokenState.check_token.set()
        await message.answer(
            "Ввведите его пожалуйста, или перешлите сообщение с кодом",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    elif message.text == "Нет":
        await UserTokenState.call_trainer.set()
        await message.answer(
            "Это значит, что скорее всего вы новичёк, поэтому "
            "напишите что-нибудь и я передам это главному "
            "тренеру, а он уже свяжется с вами",
            reply_markup=types.ReplyKeyboardRemove(),
        )
    elif message.text == "К началу регистрации":
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add("Да", "Нет")
        await message.answer(
            "У вас есть регистрационный код?", reply_markup=markup
        )
    else:
        await message.reply(
            "Неправельный ввод, воспользуйтесь, пожалуйста клавиатурой"
        )


async def call_trainer(message: types.Message):
    await UserTokenState.ask_token.set()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("К началу регистрации")
    await message.reply(
        "Спасибо, мы передадим сообщение тренеру", reply_markup=markup
    )


async def check_token(message: types.Message, state: FSMContext):
    if message.text.find(APP_CONF.team.general_trainer_key) != -1:
        await user_tbl.create_general_trainer(
            user_id=message.from_user.id,
            first_name="Василий",
            last_name="Сивохоп",
            phone="+380633416762",
            birthday=arrow.now().date(),
        )
        await message.reply(
            "Рады вашей регистрации , Василий Сивохоп. "
            "Нужно сделать настройку расписания. "
            "Так же следующим сообщением придёт код регистрации, перешлите "
            "его игрокам, чтобы они смогли зарегистрирооваться"
        )
        await message.answer(
            f"Код регистрации для игроков: {APP_CONF.team.team_member_key}. "
        )
        await state.reset_state()
        await PayDayState.set_pay_day.set()
        await message.answer(
            "В какой день месяца напоминать об оплате? "
            "Введите число от 1 до 31. "
            "Если в месяце меньше дней, "
            "то оповещение будет в последний день месяца"
        )

    elif message.text.find(APP_CONF.team.team_member_key) != -1:
        await UserProfileState.set_first_name.set()
        await message.reply("Спасибо. Регистрационный код верный")
        await message.answer("Пожалуйста скажите как вас зовут?")
    else:
        await message.reply(
            "Не могу прочитать регистрационный код. "
            "Повторите, пожалуйста, попытку ввода"
        )

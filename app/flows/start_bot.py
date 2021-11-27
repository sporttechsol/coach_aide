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

from app import utils
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
            await message.answer("Вы заблокированы")
        else:
            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True, selective=True
            )
            markup.add("Профайл")
            await message.answer(
                "Вы уже зарегистрированы", reply_markup=markup
            )
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
            "Неправильный ввод, воспользуйтесь, пожалуйста клавиатурой"
        )


class CallTrainer:
    def __init__(self, dp: Dispatcher):
        self.dp = dp
        self.message_to_send = None

    async def call_trainer(self, message: types.Message):
        self.message_to_send = message
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add("Да", "Нет")
        await UserTokenState.verify_trainer_message.set()
        await message.reply(
            "Вы собираетесь отправить тренеру это сообщение",
            reply_markup=markup,
        )

    async def verify_message(self, message: types.Message):
        if message.text == "Да":
            trainer = await user_tbl.get_general_trainer()

            await utils.forward_message(
                self.dp, trainer.user_id, self.message_to_send
            )
            reply = "Спасибо, мы передадим сообщение тренеру"
        elif message.text == "Нет":
            reply = "Мы не будем отправлять это сообщение."
        else:
            reply = "Ответ не распознан. Воспользуейтесь кнопками."

        await UserTokenState.ask_token.set()
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, selective=True
        )
        markup.add("К началу регистрации")
        await message.answer(reply, reply_markup=markup)


async def check_token(message: types.Message, state: FSMContext):
    if message.text.find(APP_CONF.team.general_trainer_key) != -1:
        if await user_tbl.get_general_trainer():
            await message.reply(
                "Главный тренер уже зарегистрирован! "
                "Вы самозванец. Откуда у вас этот код?"
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
                f"Рады вашей регистрации , {first_name} {last_name}. "
                "Нужно сделать настройку расписания. "
                "Так же следующим сообщением придёт код регистрации, "
                "перешлите его игрокам, чтобы они смогли зарегистрирооваться"
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

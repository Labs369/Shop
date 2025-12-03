# shop_bot.py — полностью рабочий Telegram-магазин
# Копируй целиком, замени только одну строчку с TOKEN

import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

# Показывать все ошибки в логах Render
logging.basicConfig(level=logging.INFO)

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ЗАМЕНИ ЭТУ СТРОЧКУ НА СВОЙ НАСТОЯЩИЙ ТОКЕН ОТ @BotFather
TOKEN = "8070560231:AAGwQJ6OzqimPm9brVXR9aFUgqKwOAjCgnM"   # ←←←←←←←←←←←←←←←←←←←←←←←
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

# Тестовый токен платежей (без реальных денег)
PAYMENTS_TOKEN = "284685063:TEST:YjM1ZjE5ZjctMjY3Y"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Товары (меняй как хочешь)
goods = {
    "1": {"name": "Футболка белая", "price": 79900},  # 799 ₽
    "2": {"name": "Кепка чёрная",    "price": 49900},  # 499 ₽
    "3": {"name": "Носки 3 пары",   "price": 29900},  # 299 ₽
}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Это твой магазин в Telegram\n\n"
        "Нажми /menu — покажу товары"
    )

@dp.message(Command("menu"))
async def menu(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Футболка белая — 799 ₽", callback_data="buy_1")],
        [types.InlineKeyboardButton(text="Кепка чёрная — 499 ₽",    callback_data="buy_2")],
        [types.InlineKeyboardButton(text="Носки 3 пары — 299 ₽",   callback_data="buy_3")],
    ])
    await message.answer("Выбери товар:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    item_id = callback.data.split("_")[1]
    item = goods[item_id]

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Заказ в магазине",
        description=item["name"],
        payload=f"order_{item_id}_{callback.from_user.id}",
        provider_token=PAYMENTS_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=item["name"], amount=item["price"])],
        start_parameter="shop"
    )
    await callback.answer("Счёт выставлен! Нажми «Оплатить»")

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

@dp.message(lambda message: message.successful_payment)
async def success_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    item_id = payload.split("_")[1]
    await message.answer(
        f"Спасибо за покупку «{goods[item_id]['name']}»!\n"
        f"Оплачено: {message.successful_payment.total_amount // 100} ₽\n\n"
        "Скоро свяжемся для доставки\n"
        "Ещё что-нибудь? /menu"
    )

async def main():
    print("Запускаю бота...")
    try:
        me = await bot.get_me()
        print(f"Бот успешно запущен: @{me.username} ({me.first_name})")
    except Exception as e:
        print("ОШИБКА ПОДКЛЮЧЕНИЯ К TELEGRAM:")
        print(e)
        raise
    print("Бот работает 24/7 — заходи в Telegram и пиши /start")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

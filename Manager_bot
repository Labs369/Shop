# shop_bot.py
# Полный Telegram-магазин: меню → выбор товара → оплата → спасибо
# Работает на PythonAnywhere без настройки вебхуков
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

# ←←← ЗАМЕНИ НА СВОЙ ТОКЕН ОТ @BotFather ←←←
TOKEN = "8070560231:AAGwQJ6OzqimPm9brVXR9aFUgqKwOAjCgnM"
# Если хочешь платежи реальными деньгами — замени на токен от @BotFather (Payments)
# Для тестовых платежей оставь так, как есть
PAYMENTS_TOKEN = "284685063:TEST:YjM1ZjE5ZjctMjY3Y"  # тестовый токен (работает без реальных денег)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Товары (меняй названия и цены как угодно)
goods = {
    "1": {"name": "Футболка белая", "price": 79900},  # цена в копейках (799 руб.)
    "2": {"name": "Кепка чёрная", "price": 49900},     # 499 руб.
    "3": {"name": "Носки 3 пары", "price": 29900},     # 299 руб.
}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Это твой магазин прямо в Телеграме\n\n"
        "Напиши /menu чтобы посмотреть товары"
    )

@dp.message(Command("menu"))
async def menu(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Футболка белая — 799 ₽", callback_data="buy_1")],
        [types.InlineKeyboardButton(text="Кепка чёрная — 499 ₽", callback_data="buy_2")],
        [types.InlineKeyboardButton(text="Носки 3 пары — 299 ₽", callback_data="buy_3")],
    ])
    await message.answer("Выбери товар:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    item_id = callback.data.split("_")[1]
    item = goods[item_id]

    prices = [LabeledPrice(label=item["name"], amount=item["price"])]

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="Заказ в магазине",
        description=item["name"],
        payload=f"order_{item_id}_{callback.from_user.id}",
        provider_token=PAYMENTS_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="shop",
    )
    await callback.answer()

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

@dp.message(lambda message: message.successful_payment)
async def successful_payment(message: types.Message):
    await message.answer(
        "Спасибо за покупку! \n"
        "Товар уже готовится к отправке.\n"
        "Напиши /menu чтобы купить ещё что-нибудь"
    )

async def main():
    print("Бот запущен! Иди в Telegram и пиши /start")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

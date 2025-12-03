# card_shop_bot.py — именно тот самый "карточный" магазин, как на презентации
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

TOKEN = "8070560231:AAGwQJ6OzqimPm9brVXR9aFUgqKwOAjCgnM"   # ← ТВОЙ ТОКЕН
PAYMENTS_TOKEN = "284685063:TEST:YjM1ZjE5ZjctMjY3Y"       # тестовый

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ←←←←←←←←←←←←←←←←←←←←←←←←←←
# СЮДА ВСТАВЛЯЙ СВОИ ТОВАРЫ
catalog = [
    {
        "photo": "https://i.imgur.com/0t5f2kE.jpeg",           # большая красивая фотка
        "name": "Футболка Premium «Кот в космосе»",
        "desc": "• 100% хлопок\n• Печать шелкографией\n• Размеры: S–XXL\n• Цвет: чёрный и белый",
        "price": 2490_00   # 2490 ₽ (в копейках)
    },
    {
        "photo": "https://i.imgur.com/8y7hLmK.jpeg",
        "name": "Кепка Snapback",
        "desc": "• Регулируемый размер\n• Плотный козырёк\n• Вышивка спереди",
        "price": 1890_00
    },
    {
        "photo": "https://i.imgur.com/x1pR9sD.jpeg",
        "name": "Носки «Рик и Морти» (3 пары)",
        "desc": "• Высокий хлопок\n• Усиленная пятка\n• 3 пары в комплекте",
        "price": 990_00
    },
]

# Показать карточку товара по индексу
async def show_card(message_or_call, index: int):
    item = catalog[index]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="◀ Предыдущий", callback_data=f"prev_{index}"),
            types.InlineKeyboardButton(text="Купить сейчас", callback_data=f"buy_{index}"),
            types.InlineKeyboardButton(text="Следующий ▶", callback_data=f"next_{index}"),
        ]
    ])

    text = f"<b>{item['name']}</b>\n\n{item['desc']}\n\n💰 Цена: <b>{item['price']//100} ₽</b>"

    if message_or_call.photo:
        await message_or_call.edit_media(
            media=types.InputMediaPhoto(media=item["photo"], caption=text, parse_mode="HTML"),
            reply_markup=keyboard
        )
    else:
        await message_or_call.answer_photo(
            photo=item["photo"],
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

@dp.message(Command("start"))
async def start(message: types.Message):
    await show_card(message, 0)

@dp.callback_query(lambda c: c.data.startswith("prev_") or c.data.startswith("next_"))
async def navigate(call: types.CallbackQuery):
    action, idx = call.data.split("_")
    idx = int(idx)
    new_idx = (idx - 1) if action == "prev" else (idx + 1)
    if new_idx < 0:
        new_idx = len(catalog) - 1
    if new_idx >= len(catalog):
        new_idx = 0
    await show_card(call.message, new_idx)

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    item = catalog[idx]

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=item["name"],
        description=item["desc"],
        payload=f"item_{idx}",
        provider_token=PAYMENTS_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=item["name"], amount=item["price"])],
        photo_url=item["photo"],
        photo_width=512,
        photo_height=512,
    )
    await call.answer("Открываю оплату…")

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(lambda m: m.successful_payment)
async def paid(message: types.Message):
    item_idx = int(message.successful_payment.invoice_payload.split("_")[1])
    item = catalog[item_idx]
    await message.answer(
        f"Оплата прошла! Спасибо за покупку:\n\n"
        f"{item['name']}\n"
        f"Сумма: {message.successful_payment.total_amount // 100} ₽\n\n"
        f"Скоро напишем по доставке!"
    )

async def main():
    me = await bot.get_me()
    print(f"Карточный магазин запущен: @{me.username}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

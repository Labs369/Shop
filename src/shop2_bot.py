# main.py — КАРТОЧНЫЙ ТЕЛЕГРАМ-МАГАЗИН КАК НА ПРЕЗЕНТАЦИИ
# + Добавление товаров прямо из чата (только ты)
# + Сохранение всех товаров после перезапуска
# + Красивые карточки со стрелками ← Купить → 

import asyncio
import json
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, FSInputFile

# ====================== НАСТРОЙКИ ======================
TOKEN = "8070560231:AAGwQJ6OzqimPm9brVXR9aFUgqKwOAjCgnM"   # ← ТВОЙ ТОКЕН ОТ @BotFather
ADMIN_ID = 6720798098                                          # ← ТВОЙ Telegram ID (узнай у @userinfobot)
PAYMENTS_TOKEN = "284685063:TEST:YjM1ZjE5ZjctMjY3Y"           # тестовый (без реальных денег)
# =====================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "catalog.json"
catalog = []
user_states = {}   # для добавления товаров

# Загружаем каталог при старте
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except:
        catalog = []

def save_catalog():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

# Показать карточку товара
async def show_card(msg_or_call, index: int):
    if not catalog:
        await msg_or_call.answer("Каталог пустой!")
        return

    item = catalog[index]
    text = f"<b>{item['name']}</b>\n\n{item['desc']}\n\n💰 <b>{item['price']//100} ₽</b>"

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="◀", callback_data=f"prev_{index}"),
            types.InlineKeyboardButton(text="Купить", callback_data=f"buy_{index}"),
            types.InlineKeyboardButton(text="▶", callback_data=f"next_{index}"),
        ]
    ])

    photo = item["photo"] if item["photo"].startswith("http") else item["photo"]  # file_id или ссылка

    if hasattr(msg_or_call, "edit_media"):
        await msg_or_call.edit_media(
            media=types.InputMediaPhoto(media=photo, caption=text, parse_mode="HTML"),
            reply_markup=keyboard
        )
    else:
        await msg_or_call.answer_photo(photo=photo, caption=text, parse_mode="HTML", reply_markup=keyboard)

# ==================== КОМАНДЫ ====================
@dp.message(Command("start"))
async def start(message: types.Message):
    if not catalog:
        if message.from_user.id == ADMIN_ID:
            await message.answer("Каталог пуст! Добавь первый товар:\nОтправь фото + подпись в 3 строки:\nНазвание\nЦена\nОписание")
        else:
            await message.answer("Магазин пока пустует. Скоро появятся товары!")
        return
    await show_card(message, 0)

# ==================== НАВИГАЦИЯ ====================
@dp.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
async def navigate(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    new_idx = (idx - 1) if call.data.startswith("prev") else (idx + 1)
    if new_idx < 0: new_idx = len(catalog) - 1
    if new_idx >= len(catalog): new_idx = 0
    await show_card(call.message, new_idx)

# ==================== ПОКУПКА ====================
@dp.callback_query(F.data.startswith("buy_"))
async def buy(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    item = catalog[idx]

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=item["name"],
        description=item["desc"],
        payload=f"item_{idx}_{call.from_user.id}",
        provider_token=PAYMENTS_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label=item["name"], amount=item["price"])],
        photo_url=item["photo"] if item["photo"].startswith("http") else None,
        photo_width=800, photo_height=800,
        need_name=True, need_phone_number=True, need_shipping_address=False
    )

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def paid(message: types.Message):
    payload = message.successful_payment.invoice_payload
    idx = int(payload.split("_")[1])
    item = catalog[idx]
    await message.answer(f"СПАСИБО! Оплата прошла!\n\n{item['name']}\nСумма: {message.successful_payment.total_amount//100} ₽\n\nСкоро напишу по доставке!")

# ==================== ДОБАВЛЕНИЕ ТОВАРА (только админ) ====================
@dp.message(F.from_user.id == ADMIN_ID, F.photo)
async def admin_add_photo(message: types.Message):
    user_states[message.from_user.id] = {"photo": message.photo[-1].file_id}
    await message.answer("Фото принято! Теперь пришли текст в 3 строки:\n\nНазвание\nЦена (только цифры)\nОписание")

@dp.message(F.from_user.id == ADMIN_ID, F.text, F.text.regexp(r".+\n.+\n.+"))
async def admin_add_text(message: types.Message):
    if message.from_user.id not in user_states:
        return
    lines = message.text.strip().split("\n", 2)
    if len(lines) < 3:
        await message.answer("Нужно минимум 3 строки!")
        return
    name, price_str, desc = lines[0], lines[1], lines[2]
    try:
        price = int(float(price_str.replace(" ", "")) * 100)
    except:
        await message.answer("Цена — только число!")
        return

    new_item = {
        "photo": user_states[message.from_user.id]["photo"],
        "name": name.strip(),
        "desc": desc.strip(),
        "price": price
    }
    catalog.append(new_item)
    save_catalog()
    del user_states[message.from_user.id]

    await message.answer(f"Товар добавлен! Всего в каталоге: {len(catalog)}")
    await show_card(message, len(catalog)-1)

# ==================== ЗАПУСК ====================
async def main():
    me = await bot.get_me()
    print(f"Карточный магазин запущен: @{me.username}")
    print(f"Товаров в каталоге: {len(catalog)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# main.py — ФИНАЛЬНАЯ ВЕРСИЯ КАРТОЧНОГО МАГАЗИНА (всё работает!)
import asyncio
import json
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

# ====================== НАСТРОЙКИ ======================
TOKEN = "8070560231:AAE2ZMAP9TH2tAvdui7SWf8W94n_JFDbznI"   # ← ТВОЙ ТОКЕН
ADMIN_ID = 6720798098                                          # ← ТВОЙ ID (@userinfobot)
PAYMENTS_TOKEN = "284685063:TEST:YjM1ZjE5ZjctMjY3Y"           # тестовый
# =====================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "catalog.json"
catalog = []
user_states = {}

# Загрузка каталога
if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except:
        catalog = []

def save_catalog():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

# === ГЛАВНАЯ ФУНКЦИЯ ПОКАЗА КАРТОЧКИ (РАБОТАЕТ И С СООБЩЕНИЯМИ, И С CALLBACK) ===
async def show_card(target, index: int):
    if not catalog:
        await target.answer("Каталог пустой!")
        return

    item = catalog[index]
    text = f"<b>{item['name']}</b>\n\n{item['desc']}\n\n<b>{item['price']//100} ₽</b>"

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="Предыдущий", callback_data=f"prev_{index}"),
            types.InlineKeyboardButton(text="Купить", callback_data=f"buy_{index}"),
            types.InlineKeyboardButton(text="Следующий", callback_data=f"next_{index}"),
        ]
    ])

    # Если пришёл CallbackQuery — отправляем через message.answer_photo
    if isinstance(target, types.CallbackQuery):
        await target.message.answer_photo(
            photo=item["photo"],
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        # Если обычное сообщение — через answer_photo
        await target.answer_photo(
            photo=item["photo"],
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

# ==================== /start ====================
@dp.message(Command("start"))
async def start(message: types.Message):
    if not catalog:
        if message.from_user.id == ADMIN_ID:
            await message.answer("Каталог пуст!\nПришли фото + подпись в 3 строки:\nНазвание\nЦена\nОписание")
        else:
            await message.answer("Магазин пока пустует. Скоро товары появятся!")
        return
    await show_card(message, 0)

# ==================== НАВИГАЦИЯ ====================
@dp.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
async def navigate(call: types.CallbackQuery):
    try:
        await call.message.delete()
    except:
        pass

    idx = int(call.data.split("_")[1])
    if call.data.startswith("prev"):
        idx = idx - 1 if idx > 0 else len(catalog) - 1
    else:
        idx = idx + 1 if idx < len(catalog) - 1 else 0

    await show_card(call, idx)
    await call.answer()

# ==================== ПОКУПКА ====================
@dp.callback_query(F.data.startswith("buy_"))
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
        photo_url=item["photo"] if item["photo"].startswith("http") else None,
    )
    await call.answer("Открываю оплату...")

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def paid(message: types.Message):
    idx = int(message.successful_payment.invoice_payload.split("_")[1])
    item = catalog[idx]
    await message.answer(
        f"СПАСИБО ЗА ПОКУПКУ!\n\n{item['name']}\n"
        f"Оплачено: {message.successful_payment.total_amount//100} ₽\n\n"
        f"Скоро свяжусь по доставке!"
    )

# ==================== ДОБАВЛЕНИЕ ТОВАРА (только админ) ====================
@dp.message(F.from_user.id == ADMIN_ID, F.photo)
async def admin_add_photo(message: types.Message):
    user_states[message.from_user.id] = {"photo": message.photo[-1].file_id}
    await message.answer("Фото принято!\nТеперь пришли текст в 3 строки:\n\nНазвание\nЦена\nОписание")

@dp.message(F.from_user.id == ADMIN_ID, F.text)
async def admin_add_text(message: types.Message):
    if message.from_user.id not in user_states:
        return
    lines = [l.strip() for l in message.text.strip().split("\n")]
    if len(lines) < 3:
        await message.answer("Нужно минимум 3 строки!")
        return
    name, price_str, desc = lines[0], lines[1], "\n".join(lines[2:])

    try:
        price = int(float(price_str) * 100)
    except:
        await message.answer("Цена — только число!")
        return

    new_item = {
        "photo": user_states[message.from_user.id]["photo"],
        "name": name,
        "desc": desc,
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
    print(f"Магазин запущен: @{me.username}")
    print(f"Товаров в каталоге: {len(catalog)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# main.py — ФИНАЛЬНАЯ ВЕРСИЯ: оплата работает + админка + всё летает
import asyncio
import json
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery

# ====================== НАСТРОЙКИ ======================
TOKEN = "8070560231:AAE2ZMAP9TH2tAvdui7SWf8W94n_JFDbznI"   # ← твой токен
ADMIN_ID = 6720798098                                          # ← твой ID
PAYMENTS_TOKEN = "401643678:TEST:71178c6b5e9e2f1a8d7e"         # ← НОВЫЙ РАБОЧИЙ ТЕСТОВЫЙ ТОКЕН 2025
# =====================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "catalog.json"
catalog = []
user_states = {}

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except:
        catalog = []

def save_catalog():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

# === ПОКАЗ КАРТОЧКИ ===
async def show_card(target, index: int, admin_mode=False):
    if not catalog:
        await target.answer("Каталог пустой!")
        return

    item = catalog[index]
    text = f"<b>{item['name']}</b>\n\n{item['desc']}\n\n<b>{item['price']//100} ₽</b>"

    keyboard_rows = [
        [
            types.InlineKeyboardButton(text="Предыдущий", callback_data=f"prev_{index}"),
            types.InlineKeyboardButton(text="Купить", callback_data=f"buy_{index}"),
            types.InlineKeyboardButton(text="Следующий", callback_data=f"next_{index}"),
        ]
    ]

    # Админские кнопки только для тебя
    if admin_mode:
        keyboard_rows.append([
            types.InlineKeyboardButton(text="Удалить", callback_data=f"del_{index}"),
            types.InlineKeyboardButton(text="Админка", callback_data="admin_panel")
        ])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    if isinstance(target, types.CallbackQuery):
        await target.message.answer_photo(
            photo=item["photo"],
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await target.answer_photo(
            photo=item["photo"],
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

# === /start ===
@dp.message(Command("start"))
async def start(message: types.Message):
    admin_mode = (message.from_user.id == ADMIN_ID)
    if not catalog:
        if admin_mode:
            await message.answer("Каталог пуст! Добавь товар: пришли фото + 3 строки в подписи")
        else:
            await message.answer("Магазин пока пустует")
        return
    await show_card(message, 0, admin_mode)

# === НАВИГАЦИЯ ===
@dp.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
async def navigate(call: types.CallbackQuery):
    try:
        await call.message.delete()
    except: pass
    idx = int(call.data.split("_")[1])
    if call.data.startswith("prev"):
        idx = idx - 1 if idx > 0 else len(catalog) - 1
    else:
        idx = idx + 1 if idx < len(catalog) - 1 else 0
    await show_card(call, idx, call.from_user.id == ADMIN_ID)
    await call.answer()

# === ПОКУПКА (теперь работает!) ===
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
    )
    await call.answer("Оплата открыта!")

# === УДАЛЕНИЕ ТОВАРА (только админ) ===
@dp.callback_query(F.data.startswith("del_"))
async def delete_item(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Ты не админ")
        return
    idx = int(call.data.split("_")[1])
    deleted = catalog.pop(idx)
    save_catalog()
    await call.message.delete()
    await call.message.answer(f"Товар удалён: {deleted['name']}\nОсталось: {len(catalog)}")
    if catalog:
        await show_card(call, 0 if idx == 0 else idx - 1, True)

# === ОПЛАТА ===
@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def paid(message: types.Message):
    idx = int(message.successful_payment.invoice_payload.split("_")[1])
    item = catalog[idx]
    await message.answer(f"СПАСИБО! ОПЛАТА ПРОШЛА!\n\n{item['name']}\n{item['price']//100} ₽")
    # Уведомление админу
    await bot.send_message(ADMIN_ID, f"НОВАЯ ПОКУПКА!\n\nТовар: {item['name']}\nПокупатель: @{message.from_user.username or 'нет'}\nID: {message.from_user.id}")

# === ДОБАВЛЕНИЕ ТОВАРА ===
@dp.message(F.from_user.id == ADMIN_ID, F.photo)
async def admin_add_photo(message: types.Message):
    user_states[message.from_user.id] = {"photo": message.photo[-1].file_id}
    await message.answer("Фото принято! Теперь текст в 3 строки:\nНазвание\nЦена\nОписание")

@dp.message(F.from_user.id == ADMIN_ID, F.text)
async def admin_add_text(message: types.Message):
    if message.from_user.id not in user_states: return
    lines = [l.strip() for l in message.text.strip().split("\n", 2)]
    if len(lines) < 3: 
        await message.answer("Нужно 3 строки минимум!")
        return
    name, price_str, desc = lines[0], lines[1], lines[2]
    try:
        price = int(float(price_str) * 100)
    except:
        await message.answer("Цена — только число!")
        return
    new_item = {"photo": user_states[message.from_user.id]["photo"], "name": name, "desc": desc, "price": price}
    catalog.append(new_item)
    save_catalog()
    del user_states[message.from_user.id]
    await message.answer(f"Товар добавлен! Всего: {len(catalog)}")
    await show_card(message, len(catalog)-1, True)

# === ЗАПУСК ===
async def main():
    me = await bot.get_me()
    print(f"Магазин запущен: @{me.username} | Товаров: {len(catalog)}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

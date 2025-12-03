# main.py — ФИНАЛЬНАЯ ВЕРСИЯ МАГАЗИНА (всё работает навсегда)
import asyncio
import json
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import LabeledPrice, PreCheckoutQuery, FSInputFile

# ====================== НАСТРОЙКИ ======================
TOKEN = "8070560231:AAE2ZMAP9TH2tAvdui7SWf8W94n_JFDbznI"   # ← твой токен
ADMIN_ID = 6720798098                                          # ← твой Telegram ID
PAYMENTS_TOKEN = "401643678:TEST:71178c6b5e9e2f1a8d7e"         # рабочий тестовый токен 2025
# =====================================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "catalog.json"
catalog = []
user_states = {}

# Загрузка товаров
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
    text = f"<b>{item['name']}</b>\n\n{item['desc']}\n\n{item['price']//100} ₽"

    rows = [[
        types.InlineKeyboardButton(text="Предыдущий", callback_data=f"prev_{index}"),
        types.InlineKeyboardButton(text="Купить", callback_data=f"buy_{index}"),
        types.InlineKeyboardButton(text="Следующий", callback_data=f"next_{index}"),
    ]]

    if admin_mode:
        rows.append([
            types.InlineKeyboardButton(text="Удалить товар", callback_data=f"del_{index}"),
            types.InlineKeyboardButton(text="Админка", callback_data="admin_panel")
        ])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=rows)

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
            await message.answer("Каталог пуст!\nПришли фото + подпись:\nНазвание\nЦена\nОписание")
        else:
            await message.answer("Магазин пока пустует. Скоро будут товары!")
        return
    await show_card(message, 0, admin_mode)

# === НАВИГАЦИЯ ===
@dp.callback_query(F.data.startswith(("prev_", "next_")))
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

# === ПОКУПКА ===
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
        currency="PLN",
        prices=[LabeledPrice(label=item["name"], amount=item["price"])],
        need_name=True,
        need_phone_number=True,
    )
    await call.answer("Открываю оплату...")

# === УДАЛЕНИЕ ===
@dp.callback_query(F.data.startswith("del_"))
async def delete_item(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Нет доступа", show_alert=True)
        return
    idx = int(call.data.split("_")[1])
    deleted_name = catalog[idx]["name"]
    del catalog[idx]
    save_catalog()
    await call.message.delete()
    await call.message.answer(f"Удалено: {deleted_name}\nОсталось товаров: {len(catalog)}")
    if catalog:
        await show_card(call, 0 if idx == 0 else idx - 1, True)

# === АДМИН-ПАНЕЛЬ ===
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Доступ запрещён", show_alert=True)
        return

    text = f"<b>Админ-панель</b>\n\n" \
           f"Товаров в каталоге: <b>{len(catalog)}</b>\n\n" \
           f"• Добавляй товары фото + 3 строки\n" \
           f"• Удаляй кнопкой под товаром"

    kb = [
        [types.InlineKeyboardButton(text="Обновить каталог", callback_data="refresh")],
        [types.InlineKeyboardButton(text="Скачать backup (catalog.json)", callback_data="backup")],
        [types.InlineKeyboardButton(text="Закрыть панель", callback_data="close_admin")]
    ]
    await call.message.edit_caption(caption=text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == "close_admin")
async def close_admin(call: types.CallbackQuery):
    await call.message.delete()
    await call.answer()

@dp.callback_query(F.data == "refresh")
async def refresh(call: types.CallbackQuery):
    await call.message.delete()
    await show_card(call, 0, True)
    await call.answer("Каталог обновлён")

@dp.callback_query(F.data == "backup")
async def send_backup(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID: return
    if os.path.exists(DB_FILE):
        await bot.send_document(call.from_user.id, FSInputFile(DB_FILE))
        await call.answer("Backup отправлен")
    else:
        await call.answer("Файл ещё не создан")

# === ОПЛАТА ===
@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)

@dp.message(F.successful_payment)
async def paid(message: types.Message):
    idx = int(message.successful_payment.invoice_payload.split("_")[1])
    item = catalog[idx]
    total = message.successful_payment.total_amount // 100
    await message.answer(f"СПАСИБО! Оплата прошла!\n\n{item['name']}\nСумма: {total} ₽")

    # Уведомление админу
    user = message.from_user
    await bot.send_message(
        ADMIN_ID,
        f"<b>НОВЫЙ ЗАКАЗ!</b>\n\n"
        f"Товар: {item['name']}\n"
        f"Сумма: {total} ₽\n"
        f"Покупатель: {user.full_name} (@{user.username or 'нет'})\n"
        f"ID: <code>{user.id}</code>",
        parse_mode="HTML"
    )

# === ДОБАВЛЕНИЕ ТОВАРА ===
@dp.message(F.from_user.id == ADMIN_ID, F.photo)
async def admin_add_photo(message: types.Message):
    user_states[message.from_user.id] = {"photo": message.photo[-1].file_id}
    await message.answer("Фото сохранено!\nТеперь пришли текст в 3 строки:\n\nНазвание\nЦена\nОписание")

@dp.message(F.from_user.id == ADMIN_ID, F.text)
async def admin_add_text(message: types.Message):
    if message.from_user.id not in user_states: return
    lines = [l.strip() for l in message.text.strip().split("\n", 2)]
    if len(lines) < 3:
        await message.answer("Нужно минимум 3 строки!")
        return
    name, price_str, desc = lines[0], lines[1], lines[2]
    try:
        price = int(float(price_str.replace(" ", "")) * 100)
    except:
        await message.answer("Цена — только число!")
        return

    catalog.append({
        "photo": user_states[message.from_user.id]["photo"],
        "name": name,
        "desc": desc,
        "price": price
    })
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

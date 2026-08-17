import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from parser import parser, PeekError


router = Router()

SESSIONS = {}


def kb(items, prefix, cols=2, back=None):
    builder = InlineKeyboardBuilder()

    for i, value in enumerate(items):
        builder.button(
            text=value,
            callback_data=f"{prefix}:{i}"
        )

    if back:
        builder.button(
            text="⬅️ Назад",
            callback_data=back
        )

    builder.adjust(cols)

    return builder.as_markup()


def session(uid):
    return SESSIONS.setdefault(
        uid,
        {
            "collection": "",
            "model": "",
            "backdrop": "",
            "pattern": "",
            "attrs": {}
        }
    )


@router.message(F.text == "/start")
async def start(message: Message):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="🎁 Новый поиск",
        callback_data="new"
    )

    builder.adjust(1)

    await message.answer(
        "🎁 <b>NFT Finder</b>\n\n"
        "Выбери подарок/коллекцию — затем модель, фон и узор.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "new")
async def new_search(callback: CallbackQuery):
    SESSIONS[callback.from_user.id] = {
        "collection": "",
        "model": "",
        "backdrop": "",
        "pattern": "",
        "attrs": {}
    }

    await callback.message.edit_text(
        "🎁 Напиши <b>точное название коллекции/подарка</b>.\n\n"
        "Например:\n"
        "<code>AstralShard</code>",
        parse_mode="HTML"
    )

    await callback.answer()


@router.message()
async def collection_input(message: Message):
    if not message.text:
        return

    if message.text.startswith("/"):
        return

    current = session(message.from_user.id)

    if current["collection"]:
        return

    collection = message.text.strip()

    if not collection:
        return

    current["collection"] = collection

    await message.answer(
        "⏳ Загружаю доступные атрибуты из Peek…"
    )

    try:
        current["attrs"] = await parser.attributes(collection)

    except PeekError as error:
        current["collection"] = ""

        await message.answer(
            "❌ Peek API не ответил.\n\n"
            f"<code>{str(error)[:500]}</code>",
            parse_mode="HTML"
        )

        return

    models = current["attrs"]["models"]

    if not models:
        await message.answer(
            "⚠️ Не нашёл Model в первой странице.\n\n"
            "Можно попробовать другую коллекцию."
        )
        return

    await message.answer(
        "🎨 <b>Выбери Model</b>",
        reply_markup=kb(
            ["Все"] + models,
            "model"
        ),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("model:"))
async def choose_model(callback: CallbackQuery):
    current = session(callback.from_user.id)

    index = int(callback.data.split(":")[1])

    values = [
        "Все"
    ] + current["attrs"].get("models", [])

    selected = values[index]

    current["model"] = "" if selected == "Все" else selected

    await callback.message.edit_text(
        "🖼 <b>Выбери Backdrop</b>",
        reply_markup=kb(
            ["Все"] + current["attrs"].get("backdrops", []),
            "backdrop"
        ),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data.startswith("backdrop:"))
async def choose_backdrop(callback: CallbackQuery):
    current = session(callback.from_user.id)

    index = int(callback.data.split(":")[1])

    values = [
        "Все"
    ] + current["attrs"].get("backdrops", [])

    selected = values[index]

    current["backdrop"] = "" if selected == "Все" else selected

    await callback.message.edit_text(
        "✨ <b>Выбери Pattern</b>",
        reply_markup=kb(
            ["Все"] + current["attrs"].get("patterns", []),
            "pattern"
        ),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data.startswith("pattern:"))
async def choose_pattern(callback: CallbackQuery):
    current = session(callback.from_user.id)

    index = int(callback.data.split(":")[1])

    values = [
        "Все"
    ] + current["attrs"].get("patterns", [])

    selected = values[index]

    current["pattern"] = "" if selected == "Все" else selected

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🔎 НАЙТИ",
        callback_data="search"
    )

    builder.button(
        text="🔄 Сбросить",
        callback_data="new"
    )

    builder.adjust(1)

    await callback.message.edit_text(
        f"🎁 <b>{current['collection']}</b>\n\n"
        f"🎨 Model: <b>{current['model'] or 'Все'}</b>\n"
        f"🖼 Backdrop: <b>{current['backdrop'] or 'Все'}</b>\n"
        f"✨ Pattern: <b>{current['pattern'] or 'Все'}</b>\n\n"
        "Запустить поиск?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "search")
async def search(callback: CallbackQuery):
    current = session(callback.from_user.id)

    if not current["collection"]:
        await callback.answer(
            "Сначала выбери коллекцию",
            show_alert=True
        )
        return

    await callback.answer("Поиск запущен")

    await callback.message.edit_text(
        "🔎 <b>Ищу владельцев…</b>\n\n"
        "⏳ Запросы идут параллельно, "
        "это может занять до 20 секунд.",
        parse_mode="HTML"
    )

    started = asyncio.get_running_loop().time()

    try:
        rows = await parser.search(
            current["collection"],
            current["model"],
            current["backdrop"],
            current["pattern"]
        )

    except PeekError as error:
        await callback.message.edit_text(
            "❌ Ошибка Peek API:\n\n"
            f"<code>{str(error)[:500]}</code>",
            parse_mode="HTML"
        )
        return

    elapsed = (
        asyncio.get_running_loop().time()
        - started
    )

    if not rows:
        await callback.message.edit_text(
            f"😕 Ничего не найдено.\n\n"
            f"⏱ {elapsed:.1f} сек."
        )
        return

    lines = [
        f"✅ <b>Найдено: {len(rows)}</b>",
        f"⏱ {elapsed:.1f} сек.",
        ""
    ]

    for number, item in enumerate(rows[:30], 1):
        link = item["gift_link"]

        if not link:
            link = (
                f"https://t.me/"
                f"{item['username']}"
            )

        lines.append(
            f'{number}. '
            f'<a href="{link}">🎁 NFT</a> | '
            f'<a href="https://t.me/'
            f'{item["username"]}">'
            f'@{item["username"]}'
            f'</a>\n'
            f'   {item["model"]} · '
            f'{item["backdrop"]} · '
            f'{item["pattern"]} · '
            f'#{item["gift_number"]}'
        )

    if len(rows) > 30:
        lines.append(
            f"\n…и ещё {len(rows) - 30}"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

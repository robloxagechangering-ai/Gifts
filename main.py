import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update

from config import (
    BOT_TOKEN,
    WEBHOOK_HOST,
    WEBHOOK_PATH,
    PORT
)

from bot import router


logging.basicConfig(
    level=logging.INFO
)


async def health(request):
    return web.json_response(
        {
            "status": "ok",
            "service": "NFT Finder"
        }
    )


async def handle_webhook(
    request,
    bot,
    dp
):
    data = await request.json()

    update = Update.model_validate(
        data,
        context={
            "bot": bot
        }
    )

    await dp.feed_update(
        bot,
        update
    )

    return web.Response(
        text="OK"
    )


async def run():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set"
        )

    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher()

    dp.include_router(
        router
    )

    app = web.Application()

    app.router.add_get(
        "/health",
        health
    )

    runner = web.AppRunner(
        app
    )

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    if WEBHOOK_HOST:

        app.router.add_post(
            WEBHOOK_PATH,
            lambda request:
                handle_webhook(
                    request,
                    bot,
                    dp
                )
        )

        await bot.set_webhook(
            WEBHOOK_HOST + WEBHOOK_PATH,
            drop_pending_updates=True
        )

        logging.info(
            "Webhook: %s%s",
            WEBHOOK_HOST,
            WEBHOOK_PATH
        )

        await asyncio.Event().wait()

    else:

        logging.info(
            "Polling mode"
        )

        await bot.delete_webhook(
            drop_pending_updates=True
        )

        await dp.start_polling(
            bot
        )


if __name__ == "__main__":
    asyncio.run(
        run()
    )

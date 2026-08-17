import os


BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    ""
)


PEEK_API_URL = os.getenv(
    "PEEK_API_URL",
    "https://peek.tg/api/nft/gifts/search"
)


WEBHOOK_HOST = os.getenv(
    "WEBHOOK_HOST",
    ""
).rstrip("/")


PORT = int(
    os.getenv(
        "PORT",
        "10000"
    )
)


WEBHOOK_PATH = "/telegram/webhook"


SEARCH_PAGES = int(
    os.getenv(
        "SEARCH_PAGES",
        "20"
    )
)


SEARCH_CONCURRENCY = int(
    os.getenv(
        "SEARCH_CONCURRENCY",
        "8"
    )
)


REQUEST_TIMEOUT = float(
    os.getenv(
        "REQUEST_TIMEOUT",
        "12"
    )
)


IGNORE_USERNAMES = {
    x.strip().lower()
    for x in os.getenv(
        "IGNORE_USERNAMES",
        "giftstoportals,"
        "giftrelayer,"
        "telegram,"
        "durov,"
        "Major_Speakers,"
        "mrktbank,"
        "gemsrelayer,"
        "gifts_tester"
    ).split(",")
    if x.strip()
}


HEADERS = {
    "Accept": "*/*",

    "Accept-Encoding":
        "gzip, deflate, br",

    "Accept-Language":
        "en-US,en;q=0.9",

    "Referer":
        "https://peek.tg/search",

    "Origin":
        "https://peek.tg",

    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 "
        "Safari/537.36",
}

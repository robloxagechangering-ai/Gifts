import asyncio
from typing import Optional

import aiohttp

from config import (
    PEEK_API_URL,
    HEADERS,
    REQUEST_TIMEOUT,
    SEARCH_CONCURRENCY,
    SEARCH_PAGES,
    IGNORE_USERNAMES
)


class PeekError(RuntimeError):
    pass


class PeekParser:

    def __init__(self):

        self.sem = asyncio.Semaphore(
            SEARCH_CONCURRENCY
        )


    async def request(
        self,
        session,
        params
    ):

        async with self.sem:

            try:

                async with session.get(
                    PEEK_API_URL,
                    params=params,
                    headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(
                        total=REQUEST_TIMEOUT
                    )
                ) as response:

                    text = await response.text()

                    if response.status != 200:

                        raise PeekError(
                            f"HTTP {response.status}: "
                            f"{text[:300]}"
                        )

                    try:

                        return await response.json(
                            content_type=None
                        )

                    except Exception as error:

                        raise PeekError(
                            "Ответ не JSON: "
                            f"{text[:300]}"
                        ) from error

            except asyncio.TimeoutError as error:

                raise PeekError(
                    "таймаут запроса к Peek"
                ) from error

            except aiohttp.ClientError as error:

                raise PeekError(
                    f"ошибка соединения: {error}"
                ) from error


    @staticmethod
    def clean(
        item: dict
    ) -> Optional[dict]:

        username = str(
            item.get("username") or ""
        )

        username = (
            username
            .replace("t.me/", "")
            .lstrip("@")
            .strip()
        )

        if not username:
            return None

        if username.lower() in IGNORE_USERNAMES:
            return None

        gift_number = item.get(
            "giftNumber",
            0
        )

        gift_name = str(
            item.get("giftName") or ""
        )

        return {
            "username": username,

            "owner": str(
                item.get("owner") or ""
            ),

            "user_id": item.get(
                "userId",
                0
            ),

            "gift_number": gift_number,

            "gift_name": gift_name,

            "model": str(
                item.get("model") or ""
            ),

            "pattern": str(
                item.get("pattern") or ""
            ),

            "backdrop": str(
                item.get("backdrop") or ""
            ),

            "rarity_model": item.get(
                "rarityModel",
                0
            ),

            "rarity_pattern": item.get(
                "rarityPattern",
                0
            ),

            "rarity_backdrop": item.get(
                "rarityBackdrop",
                0
            ),

            "created_at": str(
                item.get("createdAt") or ""
            ),

            "gift_link": (
                f"https://t.me/nft/"
                f"{gift_name}-{gift_number}"
                if gift_name and gift_number
                else ""
            )
        }


    async def page(
        self,
        session,
        collection: str,
        page: int
    ):

        data = await self.request(
            session,
            {
                "name": collection,
                "page": page,
                "sortBy": "number",
                "sortOrder": "desc",
                "limit": 20
            }
        )

        if isinstance(data, dict):

            return data.get(
                "results",
                []
            )

        return []


    async def attributes(
        self,
        collection: str
    ):

        async with aiohttp.ClientSession() as session:

            results = await self.page(
                session,
                collection,
                1
            )

        rows = [
            item
            for item in (
                self.clean(raw)
                for raw in results
            )
            if item
        ]

        return {
            "models": sorted(
                {
                    item["model"]
                    for item in rows
                    if item["model"]
                }
            ),

            "backdrops": sorted(
                {
                    item["backdrop"]
                    for item in rows
                    if item["backdrop"]
                }
            ),

            "patterns": sorted(
                {
                    item["pattern"]
                    for item in rows
                    if item["pattern"]
                }
            )
        }


    async def search(
        self,
        collection: str,
        model: str = "",
        backdrop: str = "",
        pattern: str = ""
    ):

        async with aiohttp.ClientSession() as session:

            tasks = [
                self.page(
                    session,
                    collection,
                    page
                )
                for page in range(
                    1,
                    SEARCH_PAGES + 1
                )
            ]

            pages = await asyncio.gather(
                *tasks,
                return_exceptions=True
            )

        found = {}

        for page in pages:

            if isinstance(
                page,
                Exception
            ):
                continue

            for raw in page:

                row = self.clean(
                    raw
                )

                if not row:
                    continue

                if model and row["model"] != model:
                    continue

                if (
                    backdrop
                    and row["backdrop"] != backdrop
                ):
                    continue

                if (
                    pattern
                    and row["pattern"] != pattern
                ):
                    continue

                key = (
                    row["username"].lower(),
                    row["gift_number"]
                )

                found[key] = row

        return list(
            found.values()
        )


parser = PeekParser()

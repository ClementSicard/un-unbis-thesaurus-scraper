import asyncio
import json
import time
from typing import List

import aiohttp
import consts
from loguru import logger


async def get(url, session: aiohttp.ClientSession) -> None:
    try:
        async with session.get(url=url, headers=consts.HEADERS) as response:
            resp = await response.read()
            return json.loads(resp.decode("utf-8"))[0]
    except Exception as e:
        print("Unable to get url {} due to {}.".format(url, e))


async def download_multiple_urls(urls: List[str]):
    async with aiohttp.ClientSession() as session:
        ret = await asyncio.gather(*[get(url, session) for url in urls])

    print("Finalized all. Return is a list of len {} outputs.".format(len(ret)))

    return ret


def get_urls(urls: List[str]):
    start = time.time()
    results = asyncio.run(download_multiple_urls(urls))
    end = time.time()
    logger.success(f"Took {end-start:.2f} seconds to download {len(urls)} urls!")

    return results

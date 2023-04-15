import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import aiohttp
import requests
from loguru import logger


class FastURLDownloader:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    async def get(
        self,
        url: str,
        session: aiohttp.ClientSession,
        headers: Optional[Dict[str, Any]] = None,
        to_json: bool = False,
    ) -> None:
        try:
            async with session.get(url=url, headers=headers) as response:
                resp = await response.read()
                if to_json:
                    return json.loads(resp.decode("utf-8"))

                return resp.decode("utf-8")
        except Exception as e:
            logger.error(f"Unable to get url {url} due to {e}.")

    async def download_multiple_urls(
        self,
        urls: List[str],
        headers: Optional[Dict[str, Any]] = None,
        to_json: bool = False,
    ):
        async with aiohttp.ClientSession() as session:
            ret = await asyncio.gather(
                *[
                    self.get(
                        url=url,
                        session=session,
                        headers=headers,
                        to_json=to_json,
                    )
                    for url in urls
                ]
            )

        if self.verbose:
            logger.success(
                f"Finalized all. Return is a list of len {len(ret)} outputs."
            )

        return ret

    def get_urls(
        self,
        urls: List[str],
        headers: Optional[Dict[str, Any]] = None,
        to_json: bool = False,
    ):
        start = time.time()
        results = asyncio.run(
            self.download_multiple_urls(
                urls=urls,
                headers=headers,
                to_json=to_json,
            )
        )
        end = time.time()

        if self.verbose:
            logger.success(
                f"Took {end-start:.2f} seconds to download {len(urls)} urls!"
            )

        return results

    def get_html(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        to_json: bool = False,
    ) -> str:
        r = requests.get(url, headers=headers)
        if to_json:
            return r.json()

        return r.content.decode("utf-8")

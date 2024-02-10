import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import aiohttp
import requests
from loguru import logger

from thesaurus.consts import JSON


class FastURLDownloader:
    """
    Class to efficiently download multiple URLs in parallel using `asyncio` and `aiohttp`.
    """

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    async def get(
        self,
        url: str,
        session: aiohttp.ClientSession,
        headers: Optional[Dict[str, Any]] = None,
        toJson: bool = False,
    ) -> str | JSON:
        """
        Function to download a single url. This is a coroutine.

        Parameters
        ----------
        `url` : `str`
            URL to download
        `session` : `aiohttp.ClientSession`
            Session to use for downloading
        `headers` : `Optional[Dict[str, Any]]`, optional
            Headers to add to the request, by default `None`
        `toJson` : `bool`, optional
            Flag to transform response to JSON, by default `False`

        Returns
        -------
        `str | JSON`
            Response from the URL. If `toJson` is `True`, then the response is a
            JSON object. Otherwise, it is a string.
        """
        try:
            async with session.get(url=url, headers=headers) as response:
                resp: bytes = await response.read()
                if toJson:
                    ret: Dict[str, Any] = json.loads(resp.decode("utf-8"))
                    return ret

                return resp.decode("utf-8")
        except Exception as e:
            logger.error(f"Unable to get url {url} due to {e}.")
            raise e

    async def downloadMultipleURLs(
        self,
        urls: List[str],
        headers: Optional[Dict[str, Any]] = None,
        toJson: bool = False,
    ) -> List[str | JSON]:
        """
        Function to download multiple urls in parallel. This is a coroutine.

        Parameters
        ----------
        `urls` : `List[str]`
            List of URLs to download
        `headers` : `Optional[Dict[str, Any]]`, optional
            Headers to add to the request, by default `None`
        `toJson` : `bool`, optional
            Flag to return response as JSON, by default `False`

        Returns
        -------
        `List[str | JSON]`
            List of responses from the URLs. If `toJson` is `True`, then the response is a
            JSON object. Otherwise, it is a string.
        """
        async with aiohttp.ClientSession() as session:
            ret: List[str | JSON] = await asyncio.gather(
                *[
                    self.get(
                        url=url,
                        session=session,
                        headers=headers,
                        toJson=toJson,
                    )
                    for url in urls
                ]
            )

        if self.verbose:
            logger.success(f"Finalized all. Return is a list of len {len(ret)} outputs.")

        return ret

    def getURLs(
        self,
        urls: List[str],
        headers: Optional[Dict[str, Any]] = None,
        toJson: bool = False,
    ) -> List[str | JSON]:
        """
        Function to download multiple urls in parallel.

        Parameters
        ----------
        `urls` : `List[str]`
            List of URLs to download
        `headers` : `Optional[Dict[str, Any]]`, optional
            Headers to add to the request, by default `None`
        `toJson` : `bool`, optional
            Flag to export to JSON, by default `False`

        Returns
        -------
        `List[str | Dict[str, Any]]`
            _description_
        """
        start = time.time()
        results = asyncio.run(
            self.downloadMultipleURLs(
                urls=urls,
                headers=headers,
                toJson=toJson,
            )
        )
        end = time.time()

        if self.verbose:
            logger.success(f"Took {end-start:.2f} seconds to fetch {len(urls)} urls!")

        return results

    def getHtmlFromURL(
        self,
        url: str,
        headers: Optional[Dict[str, Any]] = None,
        toJson: bool = False,
    ) -> str | JSON:
        """
        Function to get the HTML content of a URL.

        Parameters
        ----------
        `url` : `str`
            URL to download
        `headers` : `Optional[Dict[str, Any]]`, optional
            Headers to add to the request, by default `None`
        `toJson` : `bool`, optional
            Flag to return response as a JSON, by default `False`

        Returns
        -------
        `str | JSON`
            Response from the URL. If `toJson` is `True`, then the response is a
            JSON object. Otherwise, it is a string.
        """
        r = requests.get(url, headers=headers)

        if toJson:
            j: Dict[str, Any] = r.json()
            return j

        return r.content.decode("utf-8")

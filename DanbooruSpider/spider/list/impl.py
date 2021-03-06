from httpx import URL, AsyncClient

from ..models import DanbooruImage, Ratings
from .worker import APIResult_T, DanbooruImageList_T, ListSpiderWorker


def _getRating(rating: str) -> Ratings:
    return {i.value: i for i in Ratings.__members__.values()}[rating.lower()]


def _getExt(url: str) -> str:
    path = URL(url).full_path
    name, ext = path.rsplit(".", 1)
    return ext


class DanbooruUnified(ListSpiderWorker):
    def __init__(self, url: str, **kwargs) -> None:
        self._url = URL(url)
        self.site = self._url.host
        super().__init__(**kwargs)

    async def parse(self, data: APIResult_T) -> DanbooruImageList_T:
        assert isinstance(data, list)
        return [
            DanbooruImage(
                **{
                    "id": i["id"],
                    "source": self.site,
                    "tags": [
                        j.strip()
                        for j in i["tags" if "tags" in i else "tag_string"].split(" ")
                        if j.strip()
                    ],
                    "rating": _getRating(i["rating"]),
                    "imageURL": i["file_url"],
                    "imageMD5": i["md5"],
                    "imageExt": _getExt(i["file_url"]),
                    "metadata": i.copy(),
                }
            )
            for i in data
            if ("file_url" in i)
        ]

    async def fetch(self, page: int, size: int) -> APIResult_T:
        fullURL = URL(self._url, params={"limit": size, "page": page})
        async with AsyncClient() as client:
            return await self._listDownload(client, fullURL)

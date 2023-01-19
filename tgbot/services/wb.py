import asyncio
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from tgbot.models.models import Product


# For test

# from pydantic import BaseModel, Field
# 
# 
# class Stock(BaseModel):
#     qty: int
#     wh: int
# 
# 
# class Size(BaseModel):
#     size_name: str = Field(alias="origName")
#     stocks: list[Stock]
# 
# 
# class Product(BaseModel):
#     sizes: list[Size]
# End for test


useragent = UserAgent()


async def get_src_with_link_to_img(client: httpx.AsyncClient, product_id: int, user_agent: str) -> str:
    """Получает html код по scu товара, в котором есть ссылка на фото товара"""
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,\
application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "ru-RU,ru;q=0.9,en-GB;q=0.8,en-US;q=0.7,en;q=0.6",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "upgrade-insecure-requests": "1",
        "user-agent": user_agent
    }
    response = await client.get(
        url=f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
        headers=headers,
        params={"targetUrl": "GP"},
        timeout=60
    )
    with open(f"{product_id}.html", "w") as file:
        file.write(response.text)
    return response.text


async def download_img(client: httpx.AsyncClient, user_agent: str, link: str, product_id: int | str):
    """Скачивает и сохраняет фотографию по ссылке"""
    headers = {
        "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "ru-RU,ru;q=0.9,en-GB;q=0.8,en-US;q=0.7,en;q=0.6",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "user-agent": user_agent
    }
    response = await client.get(url=link, headers=headers, timeout=120)
    with open(f"images/{product_id}.jpg", "wb") as file:
        file.write(response.content)


def get_link_to_download_img(src: str):
    """Находит ссылку на фото в html коде товара"""
    soup = BeautifulSoup(src, "lxml")
    link = soup.find("picture").find("img").get("src")
    return f"https:{link}"


async def get_product_info(product_id: int, is_download: bool = False) -> Product | None:
    """
    Возвращает информацию о продукте и скачивает фото если его еще нет
    :param product_id: scu товара
    :param is_download: если True скачивает фото
    :return: Product | None
    """
    user_agent = useragent.random
    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "user-agent": user_agent
    }
    params = {
        "spp": "0",
        "regions": "75,64,4,38,30,33,70,66,40,71,22,31,68,80,69,48,1",
        "stores": "119261,122252,122256,117673,122258,122259,121631,122466,122467,122495,122496,122498,122590,122591,\
122592,123816,123817,123818,123820,123821,123822,124093,124094,124095,124096,124097,124098,124099,124100,\
124101,124583,124584,125238,125239,125240,132318,132320,132321,125611,133917,132871,132870,132869,132829,\
133084,133618,132994,133348,133347,132709,132597,132807,132291,132012,126674,126676,127466,126679,126680,\
127014,126675,126670,126667,125186,116433,119400,507,3158,117501,120602,6158,121709,120762,124731,1699,130744,\
2737,117986,1733,686,132043",
        "pricemarginCoeff": "1.0",
        "reg": "0",
        "appType": "1",
        "offlineBonus": "0",
        "onlineBonus": "0",
        "emp": "0",
        "locale": "ru",
        "lang": "ru",
        "curr": "rub",
        "couponsGeo": "12,3,18,15,21",
        "dest": "-1075831,-72194,-287507,-283645",
        "nm": product_id
    }
    url = "https://wbxcatalog-ru.wildberries.ru/nm-2-card/catalog"
    url = 'https://card.wb.ru/cards/detail'
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        products = response.json()["data"]["products"]
        if products:
            if is_download and not Path(f"images/{product_id}.jpg").exists():
                # src = await get_src_with_link_to_img(client, product_id, user_agent)
                # link = get_link_to_download_img(src)
                folder_images = f"{str(product_id)[0:-4]}0000"
                link = f"https://images.wbstatic.net/big/new/{folder_images}/{product_id}-1.jpg"
                await download_img(client, user_agent, link, product_id)
            return Product.parse_obj(products[0])




# asyncio.run(get_product_info(79890778, True))

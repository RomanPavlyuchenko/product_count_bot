import asyncio

import httpx
from fake_useragent import UserAgent

from tgbot.models.models import Product


useragent = UserAgent()


async def get_product_info(product_id: int) -> Product | None:
    """Возвращает информацию о продукте"""
    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "user-agent": useragent.random
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
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
    products = response.json()["data"]["products"]
    if products:
        return Product.parse_obj(products[0])
    # return Product.parse_obj(response.json()["data"]["products"][0])


from tgbot.config import config

TEXTS = {
    "start": """🤖Привет, я буду вместо тебя следить за остатками твоего товара на Вайлдберриз. 
🤯Ведь самое страшное на пути к ТОПу это допустить нулевой остаток, а WB не даёт точную информацию по остаткам. 

❗️Для этого мне нужен артикул товара и колличество минимального остатка. 

❗️Как остаток будет равен числу которое ты напишешь я сообщу тебя об этом. """,
    "subscribe": """Реквизиты для оплаты

Сбер
4274320077397829
Получатель: Данил Георгиевич Е. 

Тинькофф
5536913942365459
Получатель: Данил Е. 

После оплаты нажмите на кнопку Оплатил(а)""",
    "paid": """Для подключения мне нужен Ваш id напишите, пожалуйста, этому боту @userinfobot старт. То что он вам \
ответит и чек об оплате отправьте, пожалуйста, администратору @andri_man и он подключит вас в систему робота, вы \
сможете использовать весь его функционал. Так же проконсультирует Вас и ответит на любые вопросы.

После подключения нажмите на команду \\start""",

    "not_subscribed": f"Необходимо быть подписанным на канал [Автоматизация Wildberries]({config.tg.chat_url})",
}

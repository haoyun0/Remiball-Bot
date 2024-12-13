import random
import re

from nonebot import require, get_driver
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from ..params.message_api import send_msg
from .stastic import get_G_data
from .bank import scout_storage
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
GBot = plugin_config.bot_g2

target = ['东', '南', '北', '珠海', '深圳']
systemRandom = random.SystemRandom()

kusa = 0


@scheduler.scheduled_job('cron', minute='0,30', second=4)
async def handle():
    await send_msg(GBot, user_id=chu_id, message='!G卖出 all')


@scheduler.scheduled_job('cron', minute='29,59', second=40)
async def handle():
    await scout_storage(GBot, storage_handle)


async def storage_handle(matcher: Matcher, arg: str = EventPlainText()):
    global kusa
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    await scout_storage(plugin_config.bot_g3, storage_handle_other)
    await matcher.finish()


async def storage_handle_other(matcher: Matcher, arg: str = EventPlainText()):
    G_data, turn = await get_G_data()

    global kusa
    tot = 0
    c = [0, 0, 0, 0, 0]
    for i in range(5):
        x = re.search(rf"G\({target[i]}校区\) \* (\d+)", arg)
        if x is not None:
            c[i] = int(int(x.group(1)) * G_data[i] * (0.5 + systemRandom.random()))
            tot += c[i]
            if systemRandom.random() > 1.2 - turn / 100:
                c[i] = 0

    for i in range(5):
        c[i] /= tot

    for i in range(5):
        if c[i] > 0:
            t = target[i]
            coin = int(kusa * c[i])
            invest = int(coin / G_data[i])
            await send_msg(GBot, user_id=chu_id, message=f'!G买入 {t[0]} {invest}')
    await matcher.finish()

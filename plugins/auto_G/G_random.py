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


@scheduler.scheduled_job('cron', minute='0,30', second=3)
async def handle():
    await send_msg(GBot, user_id=chu_id, message='!G卖出 all')


@scheduler.scheduled_job('cron', minute='29,59', second=40)
async def handle():
    await scout_storage(GBot, storage_handle)


async def storage_handle(matcher: Matcher, arg: str = EventPlainText()):
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))

    G = await get_G_data()

    p = []
    tot = 0
    for i in range(5):
        x = systemRandom.random() + 2
        tot += x
        p.append(x)

    for i in range(5):
        c = int(kusa * p[i] / tot)
        invest = int(c / G[i])
        # 买入
        await send_msg(GBot, user_id=chu_id, message=f'!G买入 {target[i][0]} {invest}')
    await matcher.finish()

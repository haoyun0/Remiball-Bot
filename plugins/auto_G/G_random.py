import random
import re

from nonebot import require, get_driver, on_command
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from ..params.message_api import send_msg
from ..params.rule import isInBotList
from ..params.permission import SUPERUSER
from .bank import scout_storage
from .stastic import get_G_data
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
GBot = plugin_config.bot_g2

target = ['东', '南', '北', '珠海', '深圳']
systemRandom = random.SystemRandom()

invest_reset = on_command('G_reset', rule=isInBotList([GBot]), permission=SUPERUSER)


@invest_reset.handle()
async def handle(matcher: Matcher):
    await send_msg(GBot, user_id=chu_id, message='!G卖出 all')
    await scout_storage(GBot, storage_handle)
    await matcher.finish()


async def storage_handle(matcher: Matcher, arg: str = EventPlainText()):
    G_data, _ = await get_G_data()
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    for i in range(5):
        invest = int(kusa / 5 / G_data[i])
        await send_msg(GBot, user_id=chu_id, message=f'!G买入 {target[i][0]} {invest}')
    await matcher.finish()


@scheduler.scheduled_job('cron', minute='1,31')
async def handle():
    await scout_storage(GBot, storage_handle2)


async def storage_handle2(matcher: Matcher, arg: str = EventPlainText()):
    for i in range(5):
        x = re.search(rf"G\({target[i]}校区\) \* (\d+)", arg)
        num = int(x.group(1))
        if systemRandom.random() < 0.35:
            await send_msg(GBot, user_id=chu_id, message=f'!G卖出 {target[i][0]} {round(num * 0.05)}')
    await matcher.finish()

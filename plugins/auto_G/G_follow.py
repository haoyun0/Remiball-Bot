import re
from datetime import datetime, timedelta

from nonebot import on_regex, require, get_driver
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot
)
from ..params.message_api import send_msg
from ..params.rule import PRIVATE, isInBotList
from ..params.permission import isInUserList
from .stastic import get_G_data
from .bank import bank_freeze
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
GBot = plugin_config.bot_main
follow_id_list = [int(x) for x in plugin_config.g_follow_accounts]
follow_id_num = 0

target = ['东', '南', '北', '珠海', '深圳']
my_kusa = 0


@scheduler.scheduled_job('cron', minute='0,30', second=3)
async def handle():
    await send_msg(GBot, user_id=chu_id, message='!G卖出 all')


@scheduler.scheduled_job('cron', minute='29,59', second=20)
async def handle():
    await bank_freeze()
    _ = on_regex(r'当前拥有草: \d+\n',
                 rule=PRIVATE() & isInBotList([GBot]), permission=isInUserList([chu_id]), block=True,
                 temp=True, handlers=[storage_handle], expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(GBot, user_id=chu_id, message='!仓库')


async def storage_handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    global my_kusa, follow_id_num
    my_kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    follow_id_num = 0

    _ = on_regex(r'当前拥有草: \d+\n',
                 rule=PRIVATE() & isInBotList([GBot]), permission=isInUserList([chu_id]), block=True,
                 temp=True, handlers=[storage_handle_other], expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(bot, user_id=chu_id, message=f'!仓库 qq={follow_id_list[follow_id_num]}')
    await matcher.finish()


async def storage_handle_other(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    G_data = await get_G_data()
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    global my_kusa, follow_id_num
    tot = 0
    c = [0, 0, 0, 0, 0]
    for i in range(5):
        x = re.search(rf"G\({target[i]}校区\) \* (\d+)", arg)
        if x is not None:
            c[i] = int(int(x.group(1)) * G_data[i])
            tot += c[i]

    if tot / (tot + kusa) < 0.3:
        follow_id_num += 1
        if follow_id_num < len(follow_id_list):
            _ = on_regex(r'当前拥有草: \d+\n',
                         rule=PRIVATE() & isInBotList([GBot]), permission=isInUserList([chu_id]), block=True,
                         temp=True, handlers=[storage_handle_other], expire_time=datetime.now() + timedelta(seconds=5))
            await send_msg(bot, user_id=chu_id, message=f'!仓库 qq={follow_id_list[follow_id_num]}')
            await matcher.finish()
        else:
            c = [0, 0, 0, 0, 0]
    else:
        for i in range(5):
            c[i] /= tot

    for i in range(5):
        if c[i] > 0:
            t = target[i]
            coin = int(my_kusa * c[i])
            invest = int(coin / G_data[i])
            await send_msg(bot, user_id=chu_id, message=f'!G买入 {t[0]} {invest}')
    await matcher.finish()

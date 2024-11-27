from datetime import datetime, timedelta

from nonebot import on_regex, require
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot
)
from ..params.message_api import send_msg
from ..params.rule import isInUserList, PRIVATE, isInBotList
from .stastic import get_G_data
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")

chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
GBot = 3584213919
follow_id = 3404416744
admin_list = [323690346, 847360401, 3584213919, 3345744507]

target = ['东', '南', '北', '珠海', '深圳']
my_kusa = 0


@scheduler.scheduled_job('cron', minute='0,30', second=3)
async def handle():
    await send_msg(GBot, user_id=chu_id, message='!G卖出 all')


@scheduler.scheduled_job('cron', minute='29,59', second=20)
async def handle():
    _ = on_regex(r'当前拥有草: \d+\n', rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([GBot]),
                 temp=True, handlers=[storage_handle], expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(GBot, user_id=chu_id, message='!仓库')


async def storage_handle(matcher: Matcher, arg: str = EventPlainText()):
    global my_kusa
    tmp = arg.index('当前拥有草: ')
    my_kusa = int(arg[tmp + 7: arg.index('\n', tmp)])

    _ = on_regex(r'当前拥有草: \d+\n', rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([GBot]),
                 temp=True, handlers=[storage_handle_other], expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(GBot, user_id=chu_id, message=f'!仓库 qq={follow_id}')
    await matcher.finish()


async def storage_handle_other(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    G_data = await get_G_data()
    global my_kusa
    tot = 0
    c = [0, 0, 0, 0, 0]
    for i in range(5):
        t = target[i]
        t2 = f"G({t}校区) * "
        if t2 in arg:
            tmp = arg.index(t2) + len(t2)
            num = 0
            while arg[tmp].isdigit():
                num = num * 10 + int(arg[tmp])
                tmp += 1
            c[i] = int(num * G_data[i])
            tot += c[i]
    if tot < 100000000:
        c = [1, 1, 1, 1, 1]
        tot = 5
    for i in range(5):
        if c[i] > 0:
            t = target[i]
            coin = int(my_kusa * c[i] / tot)
            invest = int(coin / G_data[i])
            await bot.send_private_msg(user_id=chu_id, message=f'!G买入 {t[0]} {invest}')
    await matcher.finish()

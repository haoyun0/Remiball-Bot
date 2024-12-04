import json
import re

from nonebot import require, get_driver, on_command
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText, CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent
)
from ..params.message_api import send_msg, send_msg2
from ..params.rule import isInBotList
from ..params.permission import SUPERUSER
from .stastic import get_G_data
from .bank import bank_freeze, scout_storage
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
GBot = plugin_config.bot_main
follow_id_num = 0

target = ['东', '南', '北', '珠海', '深圳']
my_kusa = 0

set_follow = on_command('G跟踪', rule=isInBotList([GBot]), permission=SUPERUSER)

try:
    with open(r'C:/Data/G_follow.txt', 'r', encoding='utf-8') as f:
        follow_data = json.loads(f.read())
except:
    follow_data = {'id_list': [323690346]}
follow_id_list = follow_data['id_list']


async def savefile():
    with open(r'C:/Data/G_follow.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(follow_data))


@set_follow.handle()
async def handle(matcher: Matcher, event: MessageEvent, arg: Message = CommandArg()):
    global follow_id_list
    args = arg.extract_plain_text().strip().split()
    if len(args) == 0:
        await send_msg2(event, f"跟G名单为{follow_id_list}")
    else:
        myList = []
        for qq in args:
            myList.append(int(qq))
        follow_id_list = myList
        follow_data['id_list'] = myList
        await send_msg2(event, f"跟G名单更新为{follow_id_list}")
        await savefile()
    await matcher.finish()


@scheduler.scheduled_job('cron', minute='0,30', second=3)
async def handle():
    await send_msg(GBot, user_id=chu_id, message='!G卖出 all')


@scheduler.scheduled_job('cron', minute='29,59', second=20)
async def handle():
    await bank_freeze()
    await scout_storage(GBot, storage_handle)


async def storage_handle(matcher: Matcher, arg: str = EventPlainText()):
    global my_kusa, follow_id_num
    my_kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    follow_id_num = 0

    await scout_storage(follow_id_list[0], storage_handle_other)
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
            await scout_storage(follow_id_list[follow_id_num], storage_handle_other)
            await matcher.finish()
        else:
            return
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

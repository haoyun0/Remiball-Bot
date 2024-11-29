import asyncio
import json
import re
from datetime import datetime, timedelta

from nonebot import on_command, on_regex, require, get_driver
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot,
)
from ..params.message_api import send_msg
from ..params.rule import isInBotList, PRIVATE
from ..params.permission import SUPERUSER, isInUserList
from .stastic import get_G_data
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
GBot = plugin_config.bot_g3
target = ['东', '南', '北', '珠海', '深圳']
target_change = [0.1, 0.1, 0.08, 0.1, 0.15]
lock_operate = asyncio.Lock()

invest_reset = on_command('G_reset', rule=isInBotList([GBot]), permission=SUPERUSER)

try:
    with open(r'C:/Data/G_bottom_fishing.txt', 'r', encoding='utf-8') as f:
        G_data = json.loads(f.read())
except:
    G_data = {
        "own": [0, 0, 0, 0, 0],
        "times": [0, 0, 0, 0, 0],
        "value": [0, 0, 0, 0, 0],
        "total_times": 0,
        "kusa_once": 0
    }
divide = 20
init_times = 15


async def savefile():
    with open(r'C:/Data/G_bottom_fishing.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(G_data))


@invest_reset.handle()
async def handle(matcher: Matcher, bot: Bot):
    await send_msg(bot, user_id=chu_id, message='!G卖出 all')
    _ = on_regex(r'当前拥有草: \d+\n',
                 rule=PRIVATE() & isInBotList([GBot]), permission=isInUserList([chu_id]), block=True,
                 temp=True, handlers=[storage_handle], expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(bot, user_id=chu_id, message='!仓库')
    await matcher.finish()


async def storage_handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    G = await get_G_data()
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    G_data["times_total"] = init_times * 5
    G_data["kusa_once"] = int(kusa / 5 / divide)
    for i in range(5):
        invest = int(G_data["kusa_once"] * init_times / G[i])
        G_data["own"][i] = invest
        G_data["times"][i] = init_times
        G_data["value"][i] = G[i]
        await send_msg(bot, user_id=chu_id, message=f'!G买入 {target[i][0]} {invest}')
    await savefile()
    await matcher.finish()


@scheduler.scheduled_job('cron', minute='1,31')
async def handle():
    G = await get_G_data()

    for i in range(5):
        if (G[i] - G_data["value"][i]) / G_data["value"][i] > target_change[i] / 3:
            invest = int(G_data["kusa_once"] / G[i])
            G_data["times"][i] -= 1
            G_data["own"][i] -= invest
            G_data["value"][i] = G[i]
            G_data["times_total"] -= 1
            await send_msg(GBot, user_id=chu_id, message=f'!G卖出 {target[i][0]} {invest}')
        elif (G[i] - G_data["value"][i]) / G_data["value"][i] < -target_change[i] / 3:
            if G_data["times"][i] < init_times * 2 and G_data["times_total"] < divide * 5:
                invest = int(G_data["kusa_once"] / G[i])
                G_data["times"][i] += 1
                G_data["own"][i] += invest
                G_data["value"][i] = G[i]
                G_data["times_total"] += 1
                await send_msg(GBot, user_id=chu_id, message=f'!G买入 {target[i][0]} {invest}')
    await savefile()

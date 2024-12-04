import asyncio
import json
import re

from nonebot import on_command, require, get_driver
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText, CommandArg, Depends
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    GroupMessageEvent,
)
from ..params.message_api import send_msg, send_msg2
from ..params.rule import isInBotList, Message_select_group
from ..params.permission import SUPERUSER
from .stastic import get_G_data
from .bank import get_user_true_kusa, freeze_depend, scout_storage
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
GBot = plugin_config.bot_g2
ceg_group_id = plugin_config.group_id_kusa
target = ['东', '南', '北', '珠海', '深圳']
lock_operate = asyncio.Lock()

invest_reset = on_command('G_reset', rule=isInBotList([GBot]), permission=SUPERUSER)
G_permit = on_command('G权限',
                      rule=Message_select_group(ceg_group_id) & isInBotList([GBot]))
G_buy_in = on_command('G买入',
                      rule=Message_select_group(ceg_group_id) & isInBotList([GBot]))
G_sell_out = on_command('G卖出',
                        rule=Message_select_group(ceg_group_id) & isInBotList([GBot]))
G_hold_on = on_command('G持有', aliases={'G拥有'},
                       rule=Message_select_group(ceg_group_id) & isInBotList([GBot]))
G_help = on_command('G帮助',
                    rule=Message_select_group(ceg_group_id) & isInBotList([GBot]))

try:
    with open(r'C:/Data/G_control.txt', 'r', encoding='utf-8') as f:
        G_data = json.loads(f.read())
except:
    G_data = {
        "own": [0, 0, 0, 0, 0],
        "kusa": 0
    }
operate_data = {}


async def savefile():
    with open(r'C:/Data/G_control.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(G_data))


@invest_reset.handle()
async def handle(matcher: Matcher, bot: Bot):
    await send_msg(bot, user_id=chu_id, message='!G卖出 all')
    await scout_storage(GBot, storage_handle)
    await matcher.finish()


async def storage_handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    G = await get_G_data()
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    G_data['kusa'] = kusa
    for i in range(5):
        invest = int(kusa / 5 / G[i])
        G_data['own'][i] = invest
        G_data['kusa'] -= int(invest * G[i])
        await send_msg(bot, user_id=chu_id, message=f'!G买入 {target[i][0]} {invest}')
    await savefile()
    await matcher.finish()


@scheduler.scheduled_job('cron', minute='29,59', second=50)
async def handle():
    operate_data.clear()


@G_permit.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent):
    m = await get_user_true_kusa(bot, event.user_id)
    if m < 10000000:
        outputStr = '没有权限'
    else:
        outputStr = f'您每次最多可以控制{m}草的G'
    await send_msg2(event, outputStr)
    await matcher.finish()


@G_hold_on.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent):
    G = await get_G_data()
    tot = 0
    outputStr = f'空闲的草: {G_data["kusa"]}'
    outputStr2 = '\n拥有的G:'
    for i in range(5):
        t = target[i]
        if G_data['own'][i] > 0:
            outputStr2 += f'\n{t[0]}: {round(G[i] * G_data["own"][i] / 1000000)}m'
            tot += int(G[i] * G_data["own"][i])
    outputStr2 += f'\n共计{round(tot / 100000000, 1)}亿草的G'
    outputStr += outputStr2 if tot > 0 else ""
    await send_msg2(event, outputStr)
    await matcher.finish()


@G_buy_in.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    m = await get_user_true_kusa(bot, event.user_id)
    if m < 10000000:
        await send_msg2(event, '没有权限')
        await matcher.finish()
    if G_data["kusa"] < 1000000:
        await send_msg2(event, '没有闲草')
        await matcher.finish()
    if not check_operate(event.user_id):
        await send_msg2(event, '本期操作次数达到上限')
        await matcher.finish()
    async with lock_operate:
        G = await get_G_data()
        args = arg.extract_plain_text().strip().split()
        n = len(args)
        k = 0
        operate = {}

        outputStr = f"[CQ:at,qq={event.user_id}]控制结果:"
        for x in args:
            i = 0
            while i < 5 and target[i][0] != x and target[i] != x:
                i += 1
            if i >= 5:
                outputStr += f'\n字符"{x}"识别失败'
                continue
            t = target[i]
            if t in operate:
                operate[t] += 1
            else:
                operate[t] = 1
            k += 1

        if len(operate) > 0:
            c = int(G_data['kusa'] / n)
            for t in operate:
                i = target.index(t)
                m2 = int(m * operate[t] / k)
                c2 = min(m2, c * operate[t])
                invest = int(c2 / G[i])
                await send_msg(bot, user_id=chu_id, message=f'!G买入 {t[0]} {invest}')
                G_data['own'][i] += invest
                G_data['kusa'] -= int(invest * G[i])
                outputStr += f'\n买入{int(invest * G[i])}草{t[0]}G成功'
            await savefile()
        await send_msg2(event, outputStr)
    await matcher.finish()


@G_sell_out.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    m = await get_user_true_kusa(bot, event.user_id)
    if m < 10000000:
        await send_msg2(event, '没有权限')
        await matcher.finish()
    if not check_operate(event.user_id):
        await send_msg2(event, '本期操作次数达到上限')
        await matcher.finish()

    async with lock_operate:
        G = await get_G_data()
        args = arg.extract_plain_text().strip().split()
        k = 0
        operate = {}

        outputStr = f"[CQ:at,qq={event.user_id}]控制结果:"
        for x in args:
            i = 0
            while i < 5 and target[i][0] != x and target[i] != x:
                i += 1
            if i >= 5:
                outputStr += f'\n字符"{x}"识别失败'
                continue
            t = target[i]
            if G_data['own'][i] == 0:
                outputStr += f'\n不持有{t[0]}G'
                continue
            if t in operate:
                operate[t] += 1
            else:
                operate[t] = 1
            k += 1

        if len(operate) > 0:
            for t in operate:
                i = target.index(t)
                m2 = int(m * operate[t] / k)
                c = int(G[i] * G_data['own'][i])
                invest = G_data['own'][i] if c <= m2 else int(m2 / G[i])
                await send_msg(bot, user_id=chu_id, message=f'!G卖出 {t[0]} {invest}')
                G_data['own'][i] -= invest
                G_data['kusa'] += int(invest * G[i])
                outputStr += f'\n卖出{int(invest * G[i])}草{t[0]}G成功'
            await savefile()
        await send_msg2(event, outputStr)
    await matcher.finish()


def check_operate(uid: int) -> bool:
    if uid not in operate_data:
        operate_data[uid] = 1
    else:
        operate_data[uid] += 1
    return operate_data[uid] <= 10


@G_help.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    outputStr = ("现在可以操控草行的部分持G了\n"
                 "G帮助: 查看该帮助\n"
                 "G权限: 查看自己能操控的比例\n"
                 "G持有: 查看草行持G及闲草\n"
                 "测G: 测G简洁版\n"
                 "G线图: 深G永远在上的版本\n"
                 "G买入: 控制草行闲草平均买入部分G\n"
                 "G卖出: 控制草行卖出部分G\n"
                 "买入卖出参数只支持具体G名称，不支持all")
    await send_msg2(event, outputStr)
    await matcher.finish()

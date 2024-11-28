import asyncio
import json
import re
from datetime import datetime, timedelta

from nonebot import on_command, on_regex
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText, CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    GroupMessageEvent,
)
from ..params.message_api import send_msg, send_msg2
from ..params.rule import isInUserList, isInBotList, PRIVATE, Message_select_group
from .stastic import get_G_data
from .bank import get_user_ratio

chu_id = 3056318700
GBot = 847360401
ceg_group_id = 738721109
admin_list = [323690346, 847360401, 3584213919, 3345744507]
target = ['东', '南', '北', '珠海', '深圳']
lock_operate = asyncio.Lock()

invest_reset = on_command('G_reset',
                          rule=isInUserList(admin_list) & isInBotList([GBot]))
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


async def savefile():
    with open(r'C:/Data/G_control.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(G_data))


@invest_reset.handle()
async def handle(matcher: Matcher, bot: Bot):
    await send_msg(bot, user_id=chu_id, message='!G卖出 all')
    _ = on_regex(r'当前拥有草: \d+\n', rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([GBot]),
                 temp=True, handlers=[storage_handle], expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(bot, user_id=chu_id, message='!仓库')
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


@G_permit.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    r = await get_user_ratio(event.user_id)
    r2 = min(max((r * 100) ** 2 / 2 / 100, r * 5), 1.0)
    if r2 < 0.01:
        outputStr = '没有权限'
    else:
        outputStr = f'您每次可以控制{round(r2 * 100, 1)}%的资本'
    await send_msg2(event, outputStr)
    await matcher.finish()


@G_hold_on.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    G = await get_G_data()
    outputStr = f'空闲的草: {G_data["kusa"]}'
    outputStr += '\n拥有的G:'
    for i in range(5):
        t = target[i]
        if G_data['own'][i] > 0:
            outputStr += f'\n{t[0]}: {round(G[i] * G_data["own"][i] / 1000000)}m'
    await send_msg2(event, outputStr)
    await matcher.finish()


@G_buy_in.handle()
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    r = await get_user_ratio(event.user_id)
    r2 = min(max((r * 100) ** 2 / 2 / 100, r * 5), 1.0)
    if r2 < 0.01:
        await send_msg2(event, '没有权限')
        await matcher.finish()
    if G_data["kusa"] < 1000000:
        await send_msg2(event, '没有闲草')
        await matcher.finish()

    args = arg.extract_plain_text().strip().split()
    d = len(args)
    if d > 10:
        await send_msg2(event, '操作过多')
        await matcher.finish()
    async with lock_operate:
        G = await get_G_data()
        c = int(G_data["kusa"] * r2 / d)

        outputStr = f"[CQ:at,qq={event.user_id}]控制结果:"
        for x in args:
            i = 0
            while i < 5 and target[i][0] != x and target[i] != x:
                i += 1
            if i >= 5:
                outputStr += f'\n字符"{x}"识别失败'
                continue
            t = target[i]
            invest = int(c // G[i])
            await send_msg(bot, user_id=chu_id, message=f'!G买入 {t[0]} {invest}')
            G_data['own'][i] += invest
            G_data['kusa'] -= int(invest * G[i])
            outputStr += f'\n买入{int(invest * G[i])}草{t[0]}G成功'
        await savefile()
        await send_msg2(event, outputStr)
    await matcher.finish()


@G_sell_out.handle()
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    r = await get_user_ratio(event.user_id)
    r2 = min(max((r * 100) ** 2 / 2 / 100, r * 5), 1.0)
    if r2 < 0.01:
        await send_msg2(event, '没有权限')
        await matcher.finish()

    async with lock_operate:
        G = await get_G_data()
        args = arg.extract_plain_text().strip().split()

        outputStr = f"[CQ:at,qq={event.user_id}]控制结果:"
        for x in args:
            i = 0
            while i < 5 and target[i][0] != x and target[i] != x:
                i += 1
            if i >= 5:
                outputStr += f'\n字符"{x}"识别失败'
                continue
            t = target[i]
            invest = int(G_data['own'][i] * r2)
            if invest == 0:
                outputStr += f'\n不持有或{t[0]}G过少'
                continue
            c = int(G[i] * invest)
            await send_msg(bot, user_id=chu_id, message=f'!G卖出 {t[0]} {invest}')
            G_data['own'][i] -= invest
            G_data['kusa'] += c
            outputStr += f'\n卖出{c}草{t[0]}G成功'
        await savefile()
        await send_msg2(event, outputStr)
    await matcher.finish()


@G_help.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    outputStr = ("现在可以操控草行的部分持G了\n"
                 "G帮助: 查看该帮助\n"
                 "G权限: 查看自己能操控的比例\n"
                 "G持有: 查看草行持G及闲草\n"
                 "G买入: 控制草行闲草平均买入部分G\n"
                 "G卖出: 控制草行卖出部分G\n"
                 "买入卖出参数只支持具体G名称，不支持all")
    await send_msg2(event, outputStr)
    await matcher.finish()

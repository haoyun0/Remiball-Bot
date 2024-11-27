import asyncio
import json
import random

from nonebot import on_command, on_regex
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    Bot
)
from ..params.message_api import send_msg, send_msg2
from ..params.kusa_helper import isSubAccount
from ..params.rule import isInUserList, Message_select_group, isInBotList
from .bank import get_user_ratio, get_user_num, get_total_storage, get_finance

chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
admin_list = [323690346, 847360401, 3584213919, 3345744507]
bot_bank = 3584213919

# 银行收益大于10%，则发出分红，为赚的10%，设为m
# 红包模式，抢完截止
# 非存款用户也可获得分红，但只有基础值
# 存款用户设为n
# 分红预计分为40%的基础值和60%股东值
# 基础值红包期望约为0.2m/n
# 用户比例为r
# r2 = max(min(max((r * 100) ** 2 / 4 / 100, r * 4), 1.0), 0.01)
# 额外值期望为 0.1m * r2

get_divvy = on_command('分红',
                       rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
cnt_divvy = on_regex('^新的G周期开始了！上个周期的G已经自动兑换为草。$',
                     rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]) & isInUserList([chu_id]))

try:
    with open(r'C:/Data/divvy.txt', 'r', encoding='utf-8') as f:
        bank_data = json.loads(f.read())
except:
    bank_data = {
        'divvy': 0,
        'divvy_total': 0,
        'user_list': []
    }
lock_divvy = asyncio.Lock()


async def savefile():
    with open(r'C:/Data/divvy.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(bank_data))


@get_divvy.handle()
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent):
    async with lock_divvy:
        m = bank_data['divvy_total']
        if m == 0:
            await send_msg2(event, '上期草行没有分红')
            await matcher.finish()
        t = bank_data['divvy']
        if t <= 0:
            await send_msg2(event, '来晚了，分红被领完了^ ^')
            await matcher.finish()
        if isSubAccount(str(event.user_id)):
            await send_msg2(event, f'[CQ:at,qq={event.get_user_id()}]小号不允许领分红(▼皿▼#)')
            await matcher.finish()
        if event.user_id in bank_data['user_list']:
            await send_msg2(event, '你已经领过上期分红^ ^')
            await matcher.finish()

        bank_data['user_list'].append(event.user_id)
        n = await get_user_num()
        kusa = random.randint(0, int(0.4 * m / n))
        r = await get_user_ratio(event.user_id)
        outputStr = f'[CQ:at,qq={event.get_user_id()}]\n'
        if r > 0:
            r2 = max(min(max((r * 100) ** 2 / 4 / 100, r * 4), 1.0), 0.01)
            kusa += random.randint(0, int(0.2 * m * r2))
            outputStr += (f'尊贵的股东{event.user_id}:\n'
                          f'您获得了{kusa}草的分红')
        else:
            outputStr += f'你获得了{kusa}草的草包'
        bank_data['divvy'] -= kusa
        await send_msg(bot, user_id=chu_id, message=f'!草转让 qq={event.user_id} kusa={kusa}')
        await send_msg2(event, outputStr)
        await savefile()
    await matcher.finish()


@cnt_divvy.handle()
async def handle(matcher: Matcher, bot: Bot):
    async with lock_divvy:
        bank_data['divvy_total'] = 0
        m = await get_finance()
        n = await get_total_storage()
        if m / n > 0.1:
            bank_data['divvy_total'] = int(0.1 * m)
            await send_msg(bot, group_id=ceg_group_id, message='草行小赚，记得来草行领取分红哦^ ^')
        bank_data['divvy'] = bank_data['divvy_total']
        bank_data['user_list'].clear()
        await savefile()
    await matcher.finish()

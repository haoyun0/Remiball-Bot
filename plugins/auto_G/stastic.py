import asyncio
import json
import re
from datetime import datetime, timedelta

from nonebot import require, on_regex, on_command
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent
)
from ..params.message_api import send_msg
from ..params.rule import isInUserList, isInBotList, PRIVATE, Message_select_group
from .bank import set_finance, update_kusa
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
admin_list = [323690346, 847360401, 3584213919, 3345744507]
notice_id = 323690346  # 给谁发通知
Bank_bot = 3584213919
target = ['东', '南', '北', '珠海', '深圳']
finance = {}

try:
    with open(r'C:/Data/G_data.txt', 'r', encoding='utf-8') as f:
        G_data = json.loads(f.read())
except:
    G_data = {}


async def savefile():
    with open(r'C:/Data/G_data.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(G_data))


get_G = on_regex(r'^G市有风险，炒G需谨慎！\n.*?\n?当前G值为：\n东校区',
                 rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([Bank_bot]))
G_conclude = on_regex(r'^您本周期的G市交易总结',
                      rule=PRIVATE() & isInUserList([chu_id]))
M_reset = on_command('投资初始化',
                     rule=isInUserList(admin_list) & isInBotList([Bank_bot]))
G_reset = on_regex(r'^上周期的G神为',
                   rule=Message_select_group(ceg_group_id) & isInUserList([chu_id]) & isInBotList(admin_list))


@get_G.handle()
async def handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    turn_new = 1 if '第一期' in arg else int(re.search(r'当前为本周期第(\d+)期数值。', arg).group(1))

    tmp = datetime.now() + timedelta(hours=1) - timedelta(minutes=turn_new * 30)
    date = tmp.strftime("%Y-%m-%d")
    if date not in G_data:
        G_data[date] = {}
    if str(turn_new) in G_data[date]:
        await matcher.finish()

    value_all = re.search(r'^G市有风险，炒G需谨慎！\n.*?\n?当前G值为：\n'
                          r'东校区：(\d+.\d+).*?\n南校区：(\d+.\d+).*?\n北校区：(\d+.\d+).*?\n'
                          r'珠海校区：(\d+.\d+).*?\n深圳校区：(\d+.\d+).*?\n', arg)

    outputStr = f'周期: {turn_new}'
    new_data = []

    for i in range(5):
        value_new = float(value_all.group(i + 1))
        new_data.append(value_new)
        outputStr += f', {target[i][0]}: {value_new}'

    G_data[date][str(turn_new)] = new_data
    await savefile()

    try:
        m: list[int] = [finance[admin_list[0]], finance[admin_list[1]], finance[admin_list[2]], finance[admin_list[3]]]
        await set_finance(m.copy())
        for i in range(4):
            m[i] = round(m[i] / 1000000)
        outputStr += f"\n无形: {m[0]}m, 有形: {m[1]}m, 跟G: {m[2]}m, 抄底: {m[3]}m"
    except:
        pass
    await send_msg(bot, user_id=notice_id, message=outputStr)

    await matcher.finish()


async def get_G_data():
    tmp = datetime.now()
    date = tmp.strftime("%Y-%m-%d")
    while date not in G_data:
        tmp -= timedelta(days=1)
        date = tmp.strftime("%Y-%m-%d")
    i = 145
    while str(i) not in G_data[date]:
        i -= 1
    return G_data[date][str(i)]


@scheduler.scheduled_job('cron', minute='0,30', second=3)
async def handle():
    for bot_id in admin_list:
        await send_msg(bot_id, user_id=chu_id, message='!交易总结')


@G_conclude.handle()
async def handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    finance[int(bot.self_id)] = int(re.search(r"本周期盈亏估值：(-?\d+)草。", arg).group(1))
    if bot.self_id == str(Bank_bot):
        await send_msg(bot, user_id=chu_id, message='!测G')
    await matcher.finish()


@M_reset.handle()
async def handle(mather: Matcher, bot: Bot):
    await send_msg(bot, group_id=test_group_id, message='/集资')
    await asyncio.sleep(10)
    _ = on_regex(r'当前拥有草: \d+\n', temp=True, handlers=[storage_handle],
                 rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([Bank_bot]),
                 expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(bot, user_id=chu_id, message='!仓库')
    await mather.finish()


@G_reset.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, bot: Bot, arg: str = EventPlainText()):
    if 'Tokens' in arg:
        await matcher.finish()
    await send_msg(bot, user_id=chu_id, message='!G卖出 all')
    if bot.self_id == str(Bank_bot):
        await update_kusa()
        await send_msg(bot, group_id=test_group_id, message='/集资')
        await asyncio.sleep(10)
        _ = on_regex(r'当前拥有草: \d+\n', temp=True, handlers=[storage_handle],
                     rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([Bank_bot]),
                     expire_time=datetime.now() + timedelta(seconds=5))
        await send_msg(bot, user_id=chu_id, message='!仓库')
    else:
        await send_msg(bot, user_id=chu_id, message='!交易总结')
    await matcher.finish()


async def storage_handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    gift = kusa // 4
    # 银行流动资金
    for uid in admin_list:
        if uid != Bank_bot:
            await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={uid} kusa={gift}")
    await send_msg(bot, user_id=chu_id, message='!交易总结')
    await asyncio.sleep(10)
    await send_msg(bot, group_id=test_group_id, message='/G_reset')
    await matcher.finish()

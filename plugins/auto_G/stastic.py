import asyncio
import json
import re
from datetime import datetime, timedelta

from nonebot import require, on_regex, on_command, logger, get_driver
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent
)
from ..params.message_api import send_msg, send_msg2
from ..params.rule import isInBotList, PRIVATE, Message_select_group
from ..params.permission import isInUserList, SUPERUSER
from .bank import set_finance, update_kusa, bank_unfreeze, get_bank_divvy, set_bank_kusa, scout_storage
from .G_pic import draw_G_pic
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
ceg_group_id = plugin_config.group_id_kusa
test_group_id = plugin_config.group_id_test
notice_id = plugin_config.bot_g1  # 给谁发通知
Bank_bot = plugin_config.bot_main
target = ['东', '南', '北', '珠海', '深圳']
G_bot_list = [plugin_config.bot_g0, plugin_config.bot_g1, plugin_config.bot_g2, plugin_config.bot_g3]
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
                 rule=PRIVATE() & isInBotList([Bank_bot]), permission=isInUserList([chu_id]))
G_conclude = on_regex(r'^您本周期的G市交易总结',
                      rule=PRIVATE(), permission=isInUserList([chu_id]))
M_reset = on_command('投资初始化',
                     rule=isInBotList([Bank_bot]), permission=SUPERUSER)
G_reset = on_regex(r'^上周期的G神为',
                   rule=Message_select_group(ceg_group_id) & isInBotList([Bank_bot]), permission=isInUserList([chu_id]))
G_ce = on_command('测G',
                  rule=Message_select_group(ceg_group_id) & isInBotList([Bank_bot]))


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
    await draw_G_pic(G_data, reverse=float(value_all.group(5)) < 120)

    try:
        m: list[int] = [finance[G_bot_list[0]], finance[G_bot_list[1]], finance[G_bot_list[2]], finance[G_bot_list[3]]]
        await set_finance(m.copy())
        for i in range(4):
            m[i] = round(m[i] / 1000000)
        outputStr += (f"\n有形: {m[2]}m, 跟G: {m[0]}m,"
                      f"无形: {m[1]}m, 抄底: {m[3]}m")
    except:
        await send_msg(bot, user_id=notice_id, message=str(finance))
        logger.error(f'更新盈亏失败#{len(finance)}')
    await send_msg(bot, user_id=notice_id, message=outputStr)
    await bank_unfreeze()

    await matcher.finish()


async def get_G_data(last: int = 1):
    tmp = datetime.now() + timedelta(minutes=15)
    date = tmp.strftime("%Y-%m-%d")
    while date not in G_data:
        tmp -= timedelta(days=1)
        date = tmp.strftime("%Y-%m-%d")
    for i in range(145, 0, -1):
        if str(i) in G_data[date]:
            last -= 1
            if last == 0:
                return G_data[date][str(i)]
    return None


@scheduler.scheduled_job('cron', minute='0,30', second=3)
async def handle():
    await asyncio.gather(
        send_msg(plugin_config.bot_g1, user_id=chu_id, message='!交易总结'),
        send_msg(plugin_config.bot_g2, user_id=chu_id, message='!交易总结'),
        send_msg(plugin_config.bot_g3, user_id=chu_id, message='!交易总结')
    )
    await send_msg(Bank_bot, user_id=chu_id, message='!交易总结')


@G_conclude.handle()
async def handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    finance[int(bot.self_id)] = int(re.search(r"本周期盈亏估值：(-?\d+)草。", arg).group(1))
    if bot.self_id == str(Bank_bot):
        await send_msg(bot, user_id=chu_id, message='!测G')
    await matcher.finish()


@M_reset.handle()
async def handle(mather: Matcher):
    await scout_storage(Bank_bot, storage_handle)
    await mather.finish()


@G_reset.handle()
async def handle(matcher: Matcher, arg: str = EventPlainText()):
    if 'Tokens' in arg:
        await matcher.finish()
    await update_kusa()
    await scout_storage(Bank_bot, storage_handle)
    await matcher.finish()


async def storage_handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    d = await get_bank_divvy()
    await set_bank_kusa(kusa - d)
    gift = (kusa - d) // 4
    # 银行各策略资金
    for uid in bot.config.superusers:
        if uid != str(Bank_bot):
            await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={uid} kusa={gift}")
    await send_msg(Bank_bot, user_id=chu_id, message='!交易总结')
    await asyncio.sleep(10)
    await send_msg(Bank_bot, group_id=test_group_id, message='/G_reset')
    await matcher.finish()


@G_ce.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    now = await get_G_data()
    last = await get_G_data(2)
    outputStr = ""
    for i in range(5):
        outputStr += f"\n{target[i]}校区: {now[i]}"
        if last is not None:
            r = round((now[i] - last[i]) / last[i] * 100, 2)
            s = '+' if r >= 0 else ""
            outputStr += f"({s}{r}%)"
    await send_msg2(event, outputStr.strip())
    await matcher.finish()

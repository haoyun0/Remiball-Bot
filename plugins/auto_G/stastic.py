import asyncio
import json
import random
import re
from datetime import datetime, timedelta

from nonebot import require, on_command, on_regex
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventPlainText, T_State
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    Message,
    Bot
)
from ..params.message_api import send_msg, send_msg2
from ..params.kusa_helper import isSubAccount, isReceiveValid
from ..params.rule import isInUserList, Message_select_group, isInBotList, PRIVATE
from .bank import set_finance
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
admin_list = [323690346, 847360401, 3584213919, 3345744507]
GBot = 3345744507

try:
    with open(r'C:/Data/G_data.txt', 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
except:
    data = {}


async def savefile():
    with open(r'C:/Data/G_data.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(data))


get_G = on_regex(r'^G市有风险，炒G需谨慎！\n.*?\n?当前G值为：\n东校区',
                 rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([GBot]))


@get_G.handle()
async def handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    turn_new = 1 if '第一期' in arg else int(re.search(r'当前为本周期第(\d+)期数值。', arg).group(1))

    tmp = datetime.now() + timedelta(hours=1) - timedelta(minutes=turn_new * 30)
    date = tmp.strftime('')

    str1 = f'周期: {turn_new}'
    str2 = ""
    for i in range(5):
        t = target[i]
        t2 = t + '校区：'
        tmp = arg.index(t2) + 3 + len(t)
        if turn_new == 1:
            value_new = float(arg[tmp: arg.index('\n', tmp)])
        else:
            value_new = float(arg[tmp: arg.index('(', tmp)])
        G_data[i] = value_new
        if data['turn'] == turn_new:
            continue
        str1 += f', {t[0]}: {value_new}'
        if value_new > data[t]['value_max']:
            data[t]['value_max'] = value_new

        # if not init_flag and data[t]['own'] > 0:
        #     if (data[t]['value_max'] - data[t]['value_in']) / data[t]['value_in'] > target_change[i] * 2:
        #         invest = int(data['invest'] / divide / value_new)
        #         if data[t]['own'] > invest:
        #             # x = 1
        #             # while data[t]['own'] / 2 > invest * (x + 1):
        #             #     x += 1
        #             # data[t]['invest_times'] -= x
        #             # data['invest_total'] -= x
        #             # str2 += f'\n决策减仓卖出{invest * x}{t[0]}G, 买入价{data[t]["value_in"]}'
        #             # await G_send_msg(i, False, invest * x, x)
        #             # data[t]['own'] -= invest * x
        #             # data[t]['value_max'] = value_new
        #             # data[t]['value_in'] = value_new
        #             pass
        #     elif (data[t]['value_max'] - value_new) / data[t]['value_max'] > target_change[i] * 1:
        #         if value_new < data[t]['value_last']:
        #             if data[t]['invest_times'] < divide * 2 and data['invest_total'] < divide * 10:
        #                 # data[t]['invest_times'] += 1
        #                 # data['invest_total'] += 1
        #                 # invest = int(data['invest'] / divide / value_new)
        #                 # str2 += f'\n决策套牢买入{invest}{t[0]}G, 高峰{data[t]["value_max"]}'
        #                 # await G_send_msg(i, True, invest)
        #                 # data[t]['own'] += invest
        #                 # data[t]['value_max'] = value_new
        #                 # data[t]['value_in'] = value_new
        #                 pass
        # elif init_flag:
        if init_flag:
            invest = int(data[t]['coin'] * 2 / value_new)
            str2 += f'\n决策初始买入{invest}{t[0]}G'
            await G_send_msg(i, True, invest, divide * 2)
            data[t]['own'] = invest
            data[t]['value_max'] = value_new
            data[t]['value_in'] = value_new
        data[t]['value_last'] = value_new

    data['update_minute'] = datetime.now().minute
    data['update_hour'] = datetime.now().hour
    if data['turn'] == turn_new:
        await matcher.finish()
    data['turn'] = turn_new

    if not init_flag:
        await bot.send_private_msg(
            user_id=323690346,
            message=str1 + str2 + f'\n盈亏估值: '
                                  f'东南: {round(num_conclude[GBot_list[0]] / 1000000)}m, '
                                  f'北珠: {round(num_conclude[GBot_list[1]] / 1000000)}m, '
                                  f'深: {round(num_conclude[GBot_list[2]] / 1000000)}m')
    else:
        await bot.send_private_msg(user_id=323690346, message=str1 + f'\n初始化完成，每支G价{data["invest"] * 2}')
    if init_flag:
        data['invest_total'] = divide * 10
        init_flag = False
    await savefile()
    await matcher.finish()


async def get_G_data():
    pass

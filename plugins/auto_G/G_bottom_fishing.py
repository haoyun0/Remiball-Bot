import asyncio
import random
from datetime import datetime
import json

from nonebot import on_command, on_regex, require, get_bot
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText, CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent
)
from .myrule import isInUserList, PRIVATE, isInBotList, Message_select_group
from .bank import set_kusa, update_kusa, set_conclude_data
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")

chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
admin_list = [323690346, 847360401, 3584213919, 3345744507]
GBot_list = [847360401, 3584213919, 3345744507]

get_G = on_regex(r'^G市有风险，炒G需谨慎！\n.*?\n?当前G值为：\n东校区',
                 rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([3345744507]))
G_conclude = on_regex(r'^您本周期的G市交易总结',
                      rule=PRIVATE() & isInUserList([chu_id]) & isInBotList(GBot_list))
G_buy_in = on_command('G买入',
                      rule=isInUserList(admin_list) & isInBotList([GBot_list[2]]))
G_sell_out = on_command('G卖出',
                        rule=isInUserList(admin_list) & isInBotList([GBot_list[2]]))
G_hold_on = on_command('G持有', aliases={'G拥有'},
                       rule=isInUserList(admin_list) & isInBotList([GBot_list[2]]))
num_conclude = {}


async def G_init(matcher: Matcher, event: MessageEvent, bot: Bot, arg: str = EventPlainText()):
    if 'Tokens' in arg:
        await matcher.finish()
    global num_conclude
    await bot.send_private_msg(user_id=chu_id, message='!G卖出 all')
    if bot.self_id == '3345744507':
        num_conclude = {}
        await set_conclude_data(num_conclude)
        if event.user_id == chu_id:
            await update_kusa()
        await asyncio.sleep(2)
        await bot.send_group_msg(group_id=test_group_id, message='/集资')
        await asyncio.sleep(10)
        _ = on_regex(r'当前拥有草: \d+\n', rule=PRIVATE() & isInUserList([chu_id]),
                     temp=True, handlers=[storage_handle])
        await bot.send_private_msg(user_id=chu_id, message='!仓库')
        await bot.send_private_msg(user_id=323690346, message='正在初始化')
    await matcher.finish()


init_invest = on_command('投资初始化', rule=isInUserList(admin_list) & isInBotList(admin_list),
                         handlers=[G_init], aliases={'投资重置'})
G_reset = on_regex(r'^上周期的G神为',
                   rule=Message_select_group(ceg_group_id) & isInUserList([chu_id]) & isInBotList(admin_list),
                   handlers=[G_init])
init_flag = False
target = ['东', '南', '北', '珠海', '深圳']
target_init = [9.8, 9.8, 6.67, 32.0, 120.0]
target_change = [0.075, 0.1, 0.075, 0.1, 0.15]
G_data = [0.0, 0.0, 0.0, 0.0, 0.0]
divide = 3
try:
    with open(r'C:/Data/G_data.txt', 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
except:
    data = {
        'turn': -1,
        'invest': 200000000,
        'invest_total': 0,
        'kusa_free': 0,
        'update_minute': datetime.now().minute,
        'update_hour': datetime.now().hour - 1
    }
    data2 = {
        'own': 0,
        'coin': 0,
        'invest_times': 0,
        'value_in': 0,
        'value_max': 0.0,
        'value_last': 0.0
    }
    for i_x in range(5):
        data[target[i_x]] = data2.copy()


async def savefile():
    with open(r'C:/Data/G_data.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(data))


@get_G.handle()
async def handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    try:
        turn_new = int(arg[arg.index('当前为本周期第') + 7: arg.index('期数值')])
    except:
        turn_new = 1
    global init_flag, G_data
    if not init_flag:
        num_conclude[0] = int(data['invest'] * data['invest_total'] / divide) - data['kusa_free']
        await set_conclude_data(num_conclude)

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


@scheduler.scheduled_job('cron', minute='0,30', second=3)
async def handle():
    global num_conclude
    num_conclude = {}
    for bid in GBot_list:
        bot: Bot = get_bot(str(bid))
        await bot.send_private_msg(user_id=chu_id, message='!交易总结')
        await asyncio.sleep(1)


async def storage_handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    global init_flag
    tmp = arg.index('当前拥有草: ')
    kusa = int(arg[tmp + 7: arg.index('\n', tmp)])
    data['invest'] = round(kusa / 11)
    data['kusa_free'] = 0
    data['turn'] = -1
    for i in range(5):
        t = target[i]
        data[t]['coin'] = data['invest']
        data[t]['invest_times'] = 0
    await asyncio.sleep(1)
    # 银行流动资金
    await bot.send_private_msg(user_id=chu_id, message=f"!草转让 qq={GBot_list[1]} kusa={data['invest']}")
    await set_kusa(data['invest'])
    init_flag = True
    await asyncio.sleep(1)
    await bot.send_private_msg(user_id=chu_id, message='!测G')
    await matcher.finish()


@G_conclude.handle()
async def handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    tmp = arg.index('本周期盈亏估值：') + 8
    num_conclude[int(bot.self_id)] = int(arg[tmp: arg.index('草。\n', tmp)])
    if bot.self_id == '3345744507':
        await asyncio.sleep(1)
        await bot.send_private_msg(user_id=chu_id, message='!测G')
    await matcher.finish()


@G_buy_in.handle()
async def handle(matcher: Matcher, bot: Bot, arg: Message = CommandArg()):
    await get_G_data()
    args = arg.extract_plain_text().strip().split()

    d = len(args)
    if data['kusa_free'] < 1000000:
        await matcher.finish('没有闲草')
    c = data['kusa_free'] // d

    bot1: Bot = get_bot(str(GBot_list[0]))
    bot2: Bot = get_bot(str(GBot_list[1]))
    outputStr = "控制结果:"
    for x in args:
        i = 0
        while i < 5 and target[i][0] != x:
            i += 1
        if i >= 5:
            outputStr += f'\n字符"{x}"识别失败'
            continue
        t = target[i]
        invest = int(c // G_data[i])
        if i < 2:
            await bot.send_private_msg(user_id=chu_id, message=f'!草转让 qq={GBot_list[0]} kusa={c}')
            await asyncio.sleep(2)
            await bot1.send_private_msg(user_id=chu_id, message=f'!G买入 {t[0]} {invest}')
        elif i < 4:
            await bot.send_private_msg(user_id=chu_id, message=f'!草转让 qq={GBot_list[1]} kusa={c}')
            await asyncio.sleep(2)
            await bot2.send_private_msg(user_id=chu_id, message=f'!G买入 {t[0]} {invest}')
        else:
            await bot.send_private_msg(user_id=chu_id, message=f'!G买入 {t[0]} {invest}')
        await asyncio.sleep(2)
        data[t]['own'] += invest
        data['kusa_free'] -= c
        outputStr += f'\n买入{t[0]}G成功'
    num_conclude[0] = int(data['invest'] * data['invest_total'] / divide) - data['kusa_free']
    await set_conclude_data(num_conclude)
    await savefile()
    await matcher.finish(outputStr)


@G_sell_out.handle()
async def handle(matcher: Matcher, bot: Bot, arg: Message = CommandArg()):
    await get_G_data()
    args = arg.extract_plain_text().strip().split()

    bot1: Bot = get_bot(str(GBot_list[0]))
    bot2: Bot = get_bot(str(GBot_list[1]))
    outputStr = "控制结果:"
    for x in args:
        i = 0
        while i < 5 and target[i][0] != x:
            i += 1
        if i >= 5:
            outputStr += f'\n字符"{x}"识别失败'
            continue
        t = target[i]
        c = int(G_data[i] * data[t]['own'])
        if data[t]['own'] == 0:
            outputStr += f'\n不持有{t[0]}G'
            continue
        if i < 2:
            await bot1.send_private_msg(user_id=chu_id, message=f'!G卖出 {t[0]} {data[t]["own"]}')
            await asyncio.sleep(2)
            await bot1.send_private_msg(user_id=chu_id, message=f'!草转让 qq={GBot_list[2]} kusa={c}')
        elif i < 4:
            await bot2.send_private_msg(user_id=chu_id, message=f'!G卖出 {t[0]} {data[t]["own"]}')
            await asyncio.sleep(2)
            await bot2.send_private_msg(user_id=chu_id, message=f'!草转让 qq={GBot_list[2]} kusa={c}')
        else:
            await bot.send_private_msg(user_id=chu_id, message=f'!G卖出 {t[0]} {data[t]["own"]}')
        await asyncio.sleep(2)
        data[t]["own"] = 0
        data['kusa_free'] += c
        outputStr += f'\n卖出{t[0]}G成功'
    num_conclude[0] = int(data['invest'] * data['invest_total'] / divide) - data['kusa_free']
    await set_conclude_data(num_conclude)
    await savefile()
    await matcher.finish(outputStr)


@G_hold_on.handle()
async def handle(matcher: Matcher):
    await get_G_data()
    outputStr = '拥有的G:'
    for i in range(5):
        t = target[i]
        if data[t]['own'] > 0:
            outputStr += f'\n{t[0]}: {round(G_data[i] * data[t]["own"] / 1000000)}m'
    await matcher.finish(outputStr)


async def get_G_data():
    bot: Bot = get_bot(str(GBot_list[2]))
    if G_data[0] == 0:
        await bot.send_private_msg(user_id=chu_id, message='!测G')
        await asyncio.sleep(4)
    return G_data


from datetime import datetime, timedelta

from nonebot import on_regex, require, get_bots, get_driver
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    MessageEvent,
    Bot
)

from ..params.message_api import send_msg
from ..params.rule import PRIVATE, Message_select_group, isInBotList
from ..params.permission import SUPERUSER, isInUserList
from .rob import add_rob, refresh_friend_list
from .kusa_group import update_rank_day, update_rank_once
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)


bot_main = plugin_config.bot_kusa
chu_id = plugin_config.bot_chu
ceg_group_id = plugin_config.group_id_kusa
test_group_id = plugin_config.group_id_test
advKusaTypeEffectMap = {'巨草': 2, '巨巨草': 3, '巨灵草': 4, '灵草': 2, '灵草II': 3,
                        '灵草III': 4, '灵草IV': 5, '灵草V': 6, '灵草VI': 7, '灵草VII': 8,
                        '灵草VIII': 9, '神灵草': 10}

finish_time = {}
buff_ling = {}
capacity = {}
testing_capacity = {}
job_sec = -1
garden = on_regex("^百草园：", rule=PRIVATE(), permission=isInUserList([chu_id]))
growing_start = on_regex("^开始生.*?草.*?。", rule=PRIVATE(), permission=isInUserList([chu_id]))
grown = on_regex("^你的.*?草.*?生了出来！", rule=PRIVATE(), permission=isInUserList([chu_id]))
day_report = on_regex("^最近24小时共生草", rule=PRIVATE(), permission=isInUserList([chu_id]))
others_grow = on_regex(
    r"^开始生.*?草.*?。(剩余时间：\d+min.*?\n预计生草完成时间：\d+:\d+|\n时光魔法吟唱中……\n.*?)\n预知：生草量为\d+",
    rule=Message_select_group(ceg_group_id) & isInBotList([bot_main]),
    permission=isInUserList([chu_id]) | SUPERUSER)
others_garden = on_regex(
    r"^百草园：\n(距离.*?草.*?长成还有\d+min|你的.*?草.*?将在一分钟内长成！)\n预计生草完成时间：\d+:\d+\n"
    r"预知：生草量为\d+.*?\n\n你选择的默认草种为：.*?草.*?\n当前的土壤承载力为：\d+",
    rule=Message_select_group(ceg_group_id) & isInBotList([bot_main]),
    permission=isInUserList([chu_id]) | SUPERUSER)


async def init(uid: int):
    if uid not in capacity:
        finish_time[uid] = datetime.now() + timedelta(minutes=1)
        buff_ling[uid] = False
        capacity[uid] = 0
        testing_capacity[uid] = False
        if uid == bot_main:
            await refresh_friend_list()


@garden.handle()
async def handle(matcher: Matcher, event: MessageEvent, bot: Bot, arg: str = EventPlainText()):
    await init(event.self_id)
    if '长成' in arg:
        if '将在一分钟内长成！' in arg:
            time_tmp = 0
        else:
            time_tmp = int(arg[arg.index('长成还有') + 4: arg.index('min')])
        finish_time[event.self_id] = datetime.now() + timedelta(minutes=time_tmp)
        if job_sec >= 0:
            sec = (job_sec - finish_time[event.self_id].second + 60) % 60
            finish_time[event.self_id] += timedelta(seconds=sec)
        spare = False
    else:
        finish_time[event.self_id] = datetime.now()
        spare = True

    if '灵性保留' in arg:
        buff_ling[event.self_id] = True
    else:
        buff_ling[event.self_id] = False
    idx_temp = arg.index('土壤承载力为：')
    capacity_tmp = int(arg[idx_temp + 7: idx_temp + 9])
    if testing_capacity[event.self_id]:
        testing_capacity[event.self_id] = False
        if capacity_tmp == capacity[event.self_id]:
            await send_msg(bot, group_id=test_group_id, message='卡承载力恢复失败')
    capacity[event.self_id] = capacity_tmp
    await bot.mark_private_msg_as_read(user_id=event.user_id)

    if spare:
        m = datetime.now().minute
        sec = datetime.now().second
        d = 33 - m
        if sec >= 40:
            d -= 1
        d = (d + 60) % 60
        if capacity[event.self_id] > 10 and d > 27 and (d > 40 or capacity[event.self_id] + (d - 27) / 3 > 15) \
                or d > 10 and capacity[event.self_id] >= 20:
            if buff_ling[event.self_id]:
                await send_msg(bot, user_id=chu_id, message="!生草 灵灵草")
            else:
                await send_msg(bot, user_id=chu_id, message="!禁用 红茶")
                await send_msg(bot, user_id=chu_id, message="!生草 不灵草")
                await send_msg(bot, user_id=chu_id, message="!启用 红茶")
    await matcher.finish()


@growing_start.handle()
async def handle(matcher: Matcher, event: MessageEvent, bot: Bot, arg: str = EventPlainText()):
    if '时光魔法吟唱中' in arg:
        time_tmp = 0
    else:
        time_tmp = int(arg[arg.index('剩余时间：') + 5: arg.index('min')])
    finish_time[event.self_id] = datetime.now() + timedelta(minutes=time_tmp + 1)
    if job_sec >= 0:
        sec = (job_sec - finish_time[event.self_id].second + 60) % 60
        finish_time[event.self_id] += timedelta(seconds=sec)
    gstr = ""
    rob = False

    if '当前承载力低' in arg:
        arg = arg[:arg.index('当前承载力低')]
    # 生草量
    if '草之精华' in arg:
        normal = arg[arg.index('生草量为') + 4:arg.index('，', arg.index('生草量为') + 4)]
    else:
        normal = arg[arg.index('生草量为') + 4:]
    kusa_num = int(normal)
    ln = len(normal)
    i = 0
    while i < ln:
        j = i + 1
        while j < ln and normal[j] == normal[i]:
            j += 1
        if j - i >= 3:
            gstr += f'\n连号: {normal[i: j]}'
            if j - i >= 4:
                rob = True
        i = j

    # 草之精华量
    desc = arg[3:arg.index('。')]
    log_str = f"{time_tmp}min\n{desc}"
    adv = 0
    if '草之精华获取量为' in arg:
        adv = int(arg[arg.index('草之精华获取量为') + 8:])
        log_str += f", {adv}草精"
        if adv >= 50:
            gstr += f'\n总量: 总草精{adv}'
            rob = True

        adv_base = adv
        if buff_ling[event.self_id]:
            adv_base /= 2
        if desc in advKusaTypeEffectMap:
            adv_base /= advKusaTypeEffectMap[desc]
        adv_base = int(adv_base)
        if adv_base >= 11:
            gstr += f'\n质量: 基础草精{adv_base}'
            rob = True

    if rob:
        await add_rob(event.self_id, finish_time[event.self_id], kusa_num, adv, desc)
    log_str += f', {kusa_num}草'

    new_capacity = capacity[event.self_id] - 1 if time_tmp > 0 else capacity[event.self_id]
    await send_msg(bot_main, group_id=test_group_id,
                   message=str(event.self_id) + ', ' + datetime.now().strftime(
                       "%H:%M, ") + log_str + gstr + f'\n剩余承载力:{new_capacity}')
    await bot.mark_private_msg_as_read(user_id=event.user_id)
    await matcher.finish()


@grown.handle()
async def handle(matcher: Matcher, event: MessageEvent, bot: Bot, arg: str = EventPlainText()):
    await init(event.self_id)
    global job_sec
    sec = datetime.now().second
    if job_sec == -1 or (sec - job_sec + 60) % 60 > 10:
        job_sec = sec
        await send_msg(bot_main, group_id=test_group_id, message=f'生草结束时点更新为sec{job_sec}')
    finish_time[event.self_id] = datetime.now()
    tmp = arg.index('获得了') + 3
    kusa = int(arg[tmp: arg.index('草', tmp)])
    if '草之精华' in arg:
        tmp = arg.index('额外获得') + 4
        kusa_adv = int(arg[tmp: arg.index('草', tmp)])
    else:
        kusa_adv = 0
    await update_rank_once(bot, kusa, kusa_adv)
    await send_msg(bot, user_id=chu_id, message='!百草园')
    await send_msg(bot, user_id=chu_id, message='!生草简报')
    await matcher.finish()


@day_report.handle()
async def handle(matcher: Matcher, event: MessageEvent, bot: Bot, arg: str = EventPlainText()):
    tmp = arg.index('收获') + 2
    kusa = int(arg[tmp: arg.index('草', tmp)])
    tmp = arg.index('收获', tmp) + 2
    kusa_adv = int(arg[tmp: arg.index('草', tmp)])
    await update_rank_day(bot, kusa, kusa_adv)
    await bot.mark_private_msg_as_read(user_id=event.user_id)
    await matcher.finish()


@scheduler.scheduled_job("cron", minute=33, second=0)
async def test_capacity():
    bots = get_bots()
    for uid in bots:
        bot: Bot = bots[uid]
        await init(int(uid))
        await send_msg(bot, user_id=chu_id, message="!百草园")


@scheduler.scheduled_job("cron", minute=33, second=45)
async def test_capacity():
    bots = get_bots()
    for uid in bots:
        bot = bots[uid]
        await init(int(uid))
        global testing_capacity
        testing_capacity[int(bot.self_id)] = True
        await send_msg(bot, user_id=chu_id, message="!百草园")


@others_grow.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, bot: Bot, arg: str = EventPlainText()):
    if 'Tokens:' in arg:
        await matcher.finish()
    sec = datetime.now().second
    if '时光魔法吟唱中' in arg:
        time_tmp = 0
    else:
        time_tmp = int(arg[arg.index('剩余时间：') + 5: arg.index('min')])
    finish_tmp = datetime.now() + timedelta(minutes=time_tmp)
    if sec >= job_sec >= 0:
        finish_tmp += timedelta(minutes=1)
    rob = False

    if '当前承载力低' in arg:
        arg = arg[:arg.index('当前承载力低') - 1]
    # 生草量
    if '草之精华' in arg:
        normal = arg[arg.index('生草量为') + 4:arg.index('，', arg.index('生草量为') + 4)]
    else:
        normal = arg[arg.index('生草量为') + 4:]
    ln = len(normal)
    kusa_num = int(normal)
    i = 0
    desc = arg[3:arg.index('。')]
    gstr = f'mark({desc})'
    while i < ln:
        j = i + 1
        while j < ln and normal[j] == normal[i]:
            j += 1
        if j - i >= 4:
            rob = True
            gstr += f'\n连号: {normal[i: j]}'
        i = j

    # 草之精华量
    adv = 0
    if '草之精华获取量为' in arg:
        adv = int(arg[arg.index('草之精华获取量为') + 8:])
        if adv >= 50:
            rob = True
            gstr += f'\n总量: 总草精{adv}'

        adv_base = adv
        if desc in advKusaTypeEffectMap:
            adv_base /= advKusaTypeEffectMap[desc]
        if desc != '不灵草':
            if adv_base % 2 == 0:
                adv_base /= 2
        adv_base = int(adv_base)
        if adv_base >= 11:
            rob = True
            gstr += f'\n质量: 基础草精{adv_base}'

    if rob:
        if event.user_id == chu_id:
            if await add_rob(0, finish_tmp, kusa_num, adv, desc):
                await send_msg(bot, group_id=event.group_id, message=f"[CQ:reply,id={event.message_id}]" + gstr)
        else:
            await send_msg(bot, group_id=event.group_id, message=f"[CQ:reply,id={event.message_id}]debug:" + gstr)
    await matcher.finish()


@others_garden.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, bot: Bot, arg: str = EventPlainText()):
    if 'Tokens:' in arg:
        await matcher.finish()
    sec = datetime.now().second
    if '将在一分钟内长成！' in arg:
        time_tmp = 0
        desc = arg[arg.index('你的') + 2: arg.index('将在一分钟内长成')]
    else:
        time_tmp = int(arg[arg.index('长成还有') + 4: arg.index('min')])
        desc = arg[arg.index('距离') + 2: arg.index('长成还有')]
    finish_tmp = datetime.now() + timedelta(minutes=time_tmp)
    if sec >= job_sec:
        finish_tmp += timedelta(minutes=1)
    rob = False

    # 生草量
    if '草之精华获取量为' in arg:
        normal = arg[arg.index('生草量为') + 4:arg.index('，', arg.index('生草量为') + 4)]
    else:
        normal = arg[arg.index('生草量为') + 4:arg.index('你选择的默认草种为') - 2]
    ln = len(normal)
    kusa_num = int(normal)
    i = 0
    gstr = f'mark({desc})'
    while i < ln:
        j = i + 1
        while j < ln and normal[j] == normal[i]:
            j += 1
        if j - i >= 4:
            rob = True
            gstr += f'\n连号: {normal[i: j]}'
        i = j

    # 草之精华量
    adv = 0
    if '草之精华获取量为' in arg:
        adv = int(arg[arg.index('草之精华获取量为') + 8:arg.index('你选择的默认草种为') - 2])
        if adv >= 50:
            rob = True
            gstr += f'\n总量: 总草精{adv}'

        adv_base = adv
        if desc in advKusaTypeEffectMap:
            adv_base /= advKusaTypeEffectMap[desc]
        if desc != '不灵草':
            if '生草数量计算详情:' in arg:
                if '灵性保留' in arg:
                    adv_base /= 2
                if '休耕肥力' in arg:
                    tmp = arg.index('休耕肥力')
                    mul = int(arg[tmp + 7])
                    adv_base /= mul
            else:
                if adv_base % 2 == 0:
                    adv_base /= 2
                if adv_base % 2 == 0:
                    adv_base /= 2
                if adv_base % 3 == 0:
                    adv_base /= 3
        adv_base = int(adv_base)
        if adv_base >= 11:
            rob = True
            gstr += f'\n质量: 基础草精{adv_base}'

    if rob:
        if event.user_id == chu_id:
            if await add_rob(0, finish_tmp, kusa_num, adv, desc):
                await send_msg(bot, group_id=event.group_id, message=f"[CQ:reply,id={event.message_id}]" + gstr)
        else:
            await send_msg(bot, group_id=event.group_id, message=f"[CQ:reply,id={event.message_id}]debug:" + gstr)
    await matcher.finish()

import random
import re
from datetime import datetime, timedelta

from nonebot import on_command, on_regex, require, get_driver
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventPlainText
from nonebot.adapters.onebot.v11 import (
    Message,
    GroupMessageEvent,
    Bot
)

from ..params.message_api import send_msg, send_msg2
from ..params.rule import isInBotList, GROUP, PRIVATE, isInUserList
from ..params.kusa_helper import isSubAccount
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
bot_id = plugin_config.bot_main
handout = on_command('发草包', rule=isInBotList([bot_id]) & GROUP())
receive = on_command('抢草包', rule=isInBotList([bot_id]) & GROUP())

envelopes = []


async def handle_receive(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    # ({userId})转让了{transferKusa}个草给你！
    r = re.search(r"^.*?\((\d+)\)转让了(\d+)个草给你！", arg)
    uid, kusa_num = r.group(1), int(r.group(2))
    for data in envelopes:
        if not data['enable'] and data['user'] == uid:
            if datetime.now() - timedelta(seconds=60) < data['startTime']:
                if kusa_num < data['nums'] * 10000:
                    await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={uid} kusa={kusa_num}")
                    await send_msg(bot, group_id=data['group_id'],
                                   message=f'[CQ:at,qq={uid}]草数不符合规范已退回原账户，需保证平均每人能分到10000草')
                    envelopes.remove(data)
                    await matcher.finish()
                else:
                    data['enable'] = True
                    data['total'] = kusa_num

                    data['startTime'] = datetime.now()
                    data['remain_kusa'] = kusa_num
                    data['remain_num'] = data['nums']
                    data['record'] = {}
                    await send_msg(bot, group_id=data['group_id'],
                                   message=f'[CQ:at,qq={uid}]已收到{kusa_num}草，发出{data["nums"]}人草包成功')
                    await matcher.finish()


@handout.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    if event.user_id == chu_id:
        await send_msg2(event, '除除不能发草包哦^ ^')
        await matcher.finish()
    args: str = arg.extract_plain_text().strip()
    argList = args.split()
    if len(argList) != 1:
        await send_msg2(event, '请在指令参数输入发送的草包个数\n'
                               '发送之后bot将开始等待60s的收款，收款数额即为本次草包总额\n'
                               '草包将持续一小时左右，多余的草会退回原账户')
        await matcher.finish()
    num = int(args)
    if num < 3:
        await send_msg2(event, '草包个数至少为3，请重新输入参数')
        await matcher.finish()
    dic = {
        'group_id': event.group_id,
        'user': event.user_id,
        'enable': False,
        'nums': num,
        'startTime': datetime.now()
    }
    envelopes.append(dic)
    _ = on_regex(r"\(\d+\)转让了\d+个草给你！",
                 rule=PRIVATE() & isInBotList([bot_id]), permission=isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive])
    await send_msg2(event, f'请将准备发的草用你的账号发给bot，作为草包总额，限时60s\n\n!草转让 qq={event.self_id} kusa=')
    await matcher.finish()


@receive.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, bot: Bot):
    if isSubAccount(event.get_user_id()):
        await send_msg2(event, f'[CQ:at,qq={event.get_user_id()}]小号不允许抢草包(▼皿▼#)')
        await matcher.finish()
    outputMsg = f'[CQ:at,qq={event.user_id}]'
    flag1 = False
    expire = []
    kusa_total_get = []
    for data in envelopes:
        if data['enable']:
            if data['remain_num'] > 0:
                flag1 = True
                if event.user_id not in data['record']:
                    data['remain_num'] -= 1
                    x = data['remain_num'] + 1

                    if x == 1:
                        data['enable'] = False
                        kusa_get = data['remain_kusa']
                    else:
                        max_kusa = min(data['remain_kusa'] - (x - 1) * 1, int(data['remain_kusa'] / x * 2))
                        kusa_get = random.randint(1, max_kusa)

                    data['record'][event.user_id] = kusa_get
                    data['remain_kusa'] -= kusa_get
                    outputMsg += f'\n你抢到了{kusa_get}草'
                    kusa_total_get.append(kusa_get)

                    if x == 1:
                        timed = datetime.now() - data['startTime']
                        s = int(timed.total_seconds())
                        luckiest = 0
                        max_kusa = 0
                        for uid in data['record']:
                            if data['record'][uid] > max_kusa:
                                max_kusa = data['record'][uid]
                                luckiest = uid
                        await send_msg(bot, group_id=data['group_id'],
                                       message=f'[CQ:at,qq={data["user"]}]发起的草包已被抢完，用时{s // 60}min{s % 60}s\n'
                                               f'[CQ:at,qq={luckiest}]是手气王，获得了{max_kusa}草')
                        expire.append(data)

    for ex in expire:
        envelopes.remove(ex)
    if len(kusa_total_get) == 0:
        if flag1:
            outputMsg += ' 你已经抢过这些草包了！'
        else:
            outputMsg += ' 当前没有草包！'
        await send_msg(bot, group_id=event.group_id, message=outputMsg)
    else:
        await send_msg(bot, group_id=event.group_id, message=outputMsg)
        for kusa in kusa_total_get:
            await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={event.user_id} kusa={kusa}")
    await matcher.finish()


@scheduler.scheduled_job("interval", minutes=5)
async def handle():
    expire = []
    for data in envelopes:
        if data['enable']:
            if datetime.now() - timedelta(minutes=60) > data['startTime']:
                data['enable'] = False
                await send_msg(bot_id, user_id=chu_id,
                               message=f"!草转让 qq={data['user']} kusa={data['remain_kusa']}")
                await send_msg(bot_id, group_id=data['group_id'],
                               message=f'[CQ:at,qq={data["user"]}]你发的草包超时未抢完\n'
                                       f'剩余{data["remain_kusa"]}已退回你的账户')
                expire.append(data)
        else:
            if datetime.now() - timedelta(seconds=60) > data['startTime']:
                expire.append(data)

    for ex in expire:
        envelopes.remove(ex)

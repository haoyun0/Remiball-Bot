import asyncio
import json
import random
import re
from datetime import datetime, timedelta
from typing import Annotated

from nonebot import require, on_command, on_regex, get_driver
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventPlainText, T_State, Depends
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    Message,
    Bot
)
from ..params.message_api import send_msg, send_msg2
from ..params.kusa_helper import isSubAccount, handleOnlyOnce
from ..params.rule import Message_select_group, isInBotList, PRIVATE
from ..params.permission import SUPERUSER, isInUserList
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
ceg_group_id = plugin_config.group_id_kusa
bot_bank = plugin_config.bot_main

freeze_flag = 0
lock_divvy = asyncio.Lock()
investigate_list = {}

lock_send_kusa = asyncio.Lock()

# 用户指令
bank_ratio = on_command('草利率',
                        rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
bank_earn = on_command('草盈亏',
                       rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
bank_user_data = on_command('草账户',
                            rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
bank_user_store = on_command('草存入',
                             rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
bank_user_take = on_command('草取出',
                            rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
bank_user_take_more = on_command('草大额取出', aliases={'草预约取出'},
                                 rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
bank_user_judge = on_command('草审批',
                             rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
bank_user_loan = on_command('草借款',
                            rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
bank_user_repayment = on_command('草还款',
                                 rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
get_divvy = on_command('分红',
                       rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
# 管理员指令
bank_kusa_query = on_command('查看草存款',
                             rule=isInBotList([bot_bank]), permission=SUPERUSER)
bank_loan_query = on_command('查看草贷款',
                             rule=isInBotList([bot_bank]), permission=SUPERUSER)
bank_query_user = on_command('查看草账户',
                             rule=isInBotList([bot_bank]), permission=SUPERUSER)
bank_loan_add = on_command('草记账',
                           rule=isInBotList([bot_bank]), permission=SUPERUSER)
bank_loan_del = on_command('草销账',
                           rule=isInBotList([bot_bank]), permission=SUPERUSER)
bank_freeze = on_command('草维护',
                         rule=isInBotList([bot_bank]), permission=SUPERUSER)
bank_kusa_update = on_command('草结算',
                              rule=isInBotList([bot_bank]), permission=SUPERUSER)
# 并非指令
cnt_divvy = on_regex('^新的G周期开始了！上个周期的G已经自动兑换为草。$',
                     rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]),
                     permission=isInUserList([chu_id]))

try:
    with open(r'C:/Data/bank.txt', 'r', encoding='utf-8') as f:
        data_raw = json.loads(f.read())
        user_data = data_raw['user']
        bank_data = data_raw['bank']
except:
    data_raw = {
        'user': {},
        'bank': {
            'finance': [0, 0, 0, 0],
            'total_storage': 0,
            'total_kusa': 0,
            'divvy': 0,
            'divvy_total': 0,
            'divvy_user_list': []
        }
    }
    user_data = data_raw['user']
    bank_data = data_raw['bank']

template_user = {
    'kusa': 0,
    'kusa_new': 0,
    'loan': 0,
    'kusa_out': 0,
    'loan_amount': 0,
    'last_kusa': 0
}

lock_conclude = asyncio.Lock()


async def savefile():
    with open(r'C:/Data/bank.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(data_raw))


async def freeze_depend(matcher: Matcher, event: MessageEvent):
    if freeze_flag > 0:
        await send_msg2(event, '草行维护中，请稍后再试')
        await matcher.finish()


async def init_user(uid: str):
    if uid not in user_data:
        user_data[uid] = {}
        for key in template_user:
            user_data[uid][key] = template_user[key]


async def update_kusa():
    bank_data['total_storage'] = 0
    for uid in user_data:
        data = user_data[uid]
        # 产生利息
        num = data['kusa'] - data['kusa_new']
        data['last_kusa'] = num
        bank_data['total_storage'] += num
        if num > 0:
            data['kusa'] += int(num * 0.006)
        data['kusa_new'] = 0
        # 预约取出
        if data['kusa_out'] > 0:
            num = data['kusa_out'] if data['kusa_out'] < data['kusa'] else data['kusa']
            data['kusa_out'] = 0
            if num > 0:
                await send_msg(bot_bank, user_id=chu_id, message=f'!草转让 qq={uid} kusa={num}')
                await send_msg(bot_bank, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}] 您预约的{num}草已取出')
                data['kusa'] -= num
    await savefile()
    if bank_data["divvy_total"] > 0:
        outputStr = f'草行发出了{bank_data["divvy_total"]}草的分红，记得来草行领取哦^ ^\n'
        for uid in user_data:
            if user_data[uid]['kusa'] / bank_data['total_storage'] > 0.1:
                outputStr += f"[CQ:at,qq={uid}]"
        await send_msg(bot_bank, group_id=ceg_group_id,
                       message=outputStr)
    await bank_unfreeze()


@bank_user_data.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    uid = event.get_user_id()
    await init_user(uid)
    data = user_data[uid]
    outputStr = f'尊敬的{uid}用户'
    outputStr += f'\n您在草行的存款为{data["kusa"]}草' if data['kusa'] > 0 else '\n您在草行没有存款'
    outputStr += f'\n其中，有{data["kusa_new"]}草是新存入的' if data['kusa_new'] > 0 else ''
    outputStr += f'\n您在草行的欠款为{data["loan"]}草' if data['loan'] > 0 else ''
    outputStr += f'\n您已预约取出{data["kusa_out"]}草' if data['kusa_out'] > 0 else ''
    await send_msg2(event, outputStr)
    await matcher.finish()


@bank_user_store.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent):
    uid = event.get_user_id()
    await init_user(uid)
    _ = on_regex(rf"^.*?\({event.user_id}\)转让了\d+个草给你！",
                 rule=PRIVATE() & isInBotList([bot_bank]), permission=isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive])
    await send_msg2(event,
                    f'请将存款用你的账号发给bot，不低于1w草，限时60s，每存一笔需要重新触发指令\n\n!草转让 qq={event.self_id} kusa=')
    await matcher.finish()


@bank_user_take.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    async with lock_send_kusa:
        uid = event.get_user_id()
        await init_user(uid)
        arg: str = arg.extract_plain_text().strip()
        if not arg.isnumeric() or int(arg) <= 0:
            await send_msg2(event, '请在指令参数输入要立即取款的数额')
            await matcher.finish()
        num = int(arg)
        if num > user_data[uid]['kusa']:
            await send_msg2(event, '余额不足')
            await matcher.finish()

        _ = on_regex(rf"^你不够草|^转让成功",
                     rule=PRIVATE() & isInBotList([bot_bank]), permission=isInUserList([chu_id]), block=True,
                     expire_time=datetime.now() + timedelta(seconds=5), temp=True, handlers=[handle_give_kusa],
                     state={'uid': uid, 'kusa': num})
        await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={uid} kusa={num}")
        await asyncio.sleep(2)
    await matcher.finish()


@bank_user_take_more.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    async with lock_send_kusa:
        uid = event.get_user_id()
        await init_user(uid)
        arg: str = arg.extract_plain_text().strip()
        if not arg.isnumeric():
            await send_msg2(event, '请在指令参数输入要立即取款的数额')
            await matcher.finish()
        num = int(arg)
        if num > user_data[uid]['kusa']:
            await send_msg2(event, '余额不足')
            await matcher.finish()
        user_data[uid]['kusa_out'] = num
        await savefile()
        await send_msg2(event, f"已将预约取款的数额设置为{num}")
        await asyncio.sleep(2)
    await matcher.finish()


@bank_earn.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent):
    async with lock_conclude:
        s = bank_data['finance'].copy()
        s.sort()
        if s[1] - s[0] > s[3] - s[2]:
            random_earn = random.randint(s[1], s[3]) + s[0] + s[1] + s[3]
        else:
            random_earn = random.randint(s[0], s[2]) + s[0] + s[2] + s[3]
        real_earn = s[0] + s[1] + s[2] + s[3]

        if event.user_id in investigate_list:
            investigate_list[event.user_id] += 1
        else:
            investigate_list[event.user_id] = 0
        exact = 0
        for uid in investigate_list:
            exact += 1.0 + 0.1 * investigate_list[uid]
        earn = int((random_earn - real_earn) / exact) + real_earn
        msg = f"草行当期盈亏可能为{round(earn / 100000000, 1)}亿草"
        await send_msg2(event, msg)
        await matcher.finish()


@bank_user_judge.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    arg: str = arg.extract_plain_text().strip()
    uid = event.get_user_id()
    await init_user(uid)
    if isSubAccount(uid):
        await send_msg2(event, '小号不允许贷草^ ^')
        await matcher.finish()
    if arg == '重审':
        user_data[uid]['loan_amount'] = 0
    if user_data[uid]['loan_amount'] > 0:
        await send_msg2(event, '已存在额度数据，若要重新审批请在指令参数加入“重审”\n'
                               f'当前额度为{user_data[uid]["loan_amount"]}')
        await matcher.finish()
    _ = on_regex(rf"^.*?\({event.user_id}\)转让了10000个草给你！",
                 rule=PRIVATE() & isInBotList([bot_bank]), permission=isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive3])
    await send_msg2(event, f'审批额度需要交10000草手续费，请复制下述指令交手续费\n'
                           f'\n!草转让 qq={event.self_id} kusa=10000')
    await matcher.finish()


@bank_user_loan.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    async with lock_send_kusa:
        uid = event.get_user_id()
        await init_user(uid)
        if user_data[uid]['loan_amount'] == 0:
            await send_msg2(event, '请先使用草审批指令审核贷草额度')
            await matcher.finish()
        arg: str = arg.extract_plain_text().strip()
        if not arg.isnumeric() or int(arg) <= 0:
            await send_msg2(event, '请在指令参数输入要贷草的数额')
            await matcher.finish()
        num = int(arg)
        if num + user_data[uid]['loan'] > user_data[uid]['loan_amount']:
            await send_msg2(event, '额度不足，若想借草请联系扫地机')
            await matcher.finish()
        _ = on_regex(rf"^你不够草|^转让成功",
                     rule=PRIVATE() & isInBotList([bot_bank]), permission=isInUserList([chu_id]), block=True,
                     expire_time=datetime.now() + timedelta(seconds=5), temp=True, handlers=[handle_give_loan],
                     state={'uid': uid, 'kusa': num})
        await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={uid} kusa={num}")
        await asyncio.sleep(2)
    await matcher.finish()


@bank_user_repayment.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent):
    uid = event.get_user_id()
    await init_user(uid)
    if user_data[uid]['loan'] == 0:
        await send_msg2(event, '您不需要还款')
        await matcher.finish()
    _ = on_regex(rf"^.*?\({event.user_id}\)转让了\d+个草给你！",
                 rule=PRIVATE() & isInBotList([bot_bank]), permission=isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive2])
    await send_msg2(event, f'您在草行的欠款为{user_data[uid]["loan"]}草\n'
                           f'请将准备的欠款用你的账号发给bot，不低于1w草每次，限时60s，每还一笔需要重新触发指令，多还的自动存款'
                           f'\n\n!草转让 qq={event.self_id} kusa=')
    await matcher.finish()


async def handle_receive(matcher: Annotated[Matcher, Depends(handleOnlyOnce, use_cache=False)],
                         bot: Bot, arg: str = EventPlainText()):
    # ({userId})转让了{transferKusa}个草给你！
    r = re.search(r"^.*?\((\d+)\)转让了(\d+)个草给你！", arg)
    uid, kusa_num = r.group(1), int(r.group(2))
    await init_user(uid)
    user_data[uid]['kusa'] += kusa_num
    user_data[uid]['kusa_new'] += kusa_num
    await savefile()
    await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]成功存入{kusa_num}草')
    await matcher.finish()


async def handle_receive2(matcher: Annotated[Matcher, Depends(handleOnlyOnce, use_cache=False)],
                          bot: Bot, arg: str = EventPlainText()):
    r = re.search(r"^.*?\((\d+)\)转让了(\d+)个草给你！", arg)
    uid, kusa_num = r.group(1), int(r.group(2))
    await init_user(uid)
    if kusa_num <= user_data[uid]['loan']:
        outputStr = f'[CQ:at,qq={uid}]成功还款{kusa_num}草'
        user_data[uid]['loan'] -= kusa_num
    else:
        outputStr = (f'[CQ:at,qq={uid}]成功还款{user_data[uid]["loan"]}草\n'
                     f'成功存入{kusa_num - user_data[uid]["loan"]}草')
        user_data[uid]['kusa'] += kusa_num - user_data[uid]["loan"]
        user_data[uid]['kusa_new'] += kusa_num - user_data[uid]["loan"]
        user_data[uid]['loan'] = 0
    await savefile()
    await send_msg(bot, group_id=ceg_group_id, message=outputStr)
    await matcher.finish()


async def handle_receive3(matcher: Annotated[Matcher, Depends(handleOnlyOnce, use_cache=False)],
                          bot: Bot, arg: str = EventPlainText()):
    r = re.search(r"^.*?\((\d+)\)转让了(\d+)个草给你！", arg)
    uid = r.group(1)
    await init_user(uid)
    await send_msg(bot, user_id=chu_id, message=f'!购买 侦察凭证 1')
    _ = on_regex(r'当前拥有草: \d+\n',
                 rule=PRIVATE() & isInBotList([bot_bank]), permission=isInUserList([chu_id]), block=True,
                 temp=True, handlers=[other_storage_handle],
                 state={'user_id': uid}, expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(bot, user_id=chu_id, message=f'!仓库 qq={uid}')
    await matcher.finish()


async def other_storage_handle(matcher: Matcher, bot: Bot, state: T_State, arg: str = EventPlainText()):
    uid = state['user_id']
    result = 0
    r = re.search(r", 草精炼厂 \* (\d+)", arg)
    if r is not None:
        factory_level = min(int(r.group(1)) // 7, 5)
        result += int(100000000 * 2.5 ** (factory_level - 1)) if factory_level > 0 else 0
    r = re.search(r", 高效草精炼指南 \* (\d+)", arg)
    if r is not None:
        tips = int(r.group(1))
        result += int(250000 * 4 ** (tips - 1) / 2)
    r = re.search(r"草地 \* (\d+)", arg)
    if r is not None:
        grass = int(r.group(1))
        result += int(120 * 1.04 ** (grass - 1) * 10)
    user_data[uid]['loan_amount'] = result
    await savefile()
    await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]经过审批，您在草行的借草额度为{result}草')
    await matcher.finish()


async def handle_give_kusa(matcher: Annotated[Matcher, Depends(handleOnlyOnce, use_cache=False)],
                           bot: Bot, state: T_State, arg: str = EventPlainText()):
    uid = state['uid']
    if '转让成功' in arg:
        user_data[uid]['kusa'] -= state['kusa']
        if state['kusa'] <= user_data[uid]['kusa_new']:
            user_data[uid]['kusa_new'] -= state['kusa']
        else:
            user_data[uid]['kusa_new'] = 0
        if user_data[uid]['kusa_out'] > user_data[uid]['kusa']:
            user_data[uid]['kusa_out'] = user_data[uid]['kusa']
        await savefile()
        await send_msg(bot, group_id=ceg_group_id, message=f"[CQ:at,qq={uid}]取出{state['kusa']}草成功")
    else:
        await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]银行流动草不足，请用大额取款取草')
    await matcher.finish()


async def handle_give_loan(matcher: Annotated[Matcher, Depends(handleOnlyOnce, use_cache=False)],
                           bot: Bot, state: T_State, arg: str = EventPlainText()):
    uid = state['uid']
    if '转让成功' in arg:
        user_data[uid]['loan'] += int(state['kusa'] * 1.01)
        await savefile()
        await send_msg(bot, group_id=ceg_group_id, message=f"[CQ:at,qq={uid}]借草{state['kusa']}成功")
    else:
        await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]银行流动草不足，若要贷草请联系扫地机')
    await matcher.finish()


@get_divvy.handle(parameterless=[Depends(freeze_depend)])
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
        if event.user_id in bank_data['divvy_user_list']:
            await send_msg2(event, '你已经领过上期分红^ ^')
            await matcher.finish()

        bank_data['divvy_user_list'].append(event.user_id)
        n = 30
        kusa = random.randint(1, int(0.2 * m * 2 / n))
        r = await get_user_ratio(bot, event.user_id)
        outputStr = f'[CQ:at,qq={event.get_user_id()}]获得了{kusa}草的草包'
        if r > 0:
            r2 = max((r * 100) ** 2 / 4 / 100, r * 4)
            r2 = max(min(r2, 1.0), 0.01)
            red = random.randint(int(0.1 * m * r2), int(0.3 * m * r2))
            outputStr += (f'\n尊贵的股东{event.user_id}:'
                          f'\n您额外获得了{red}草的分红')
            kusa += red
        bank_data['divvy'] -= kusa
        await send_msg(bot, user_id=chu_id, message=f'!草转让 qq={event.user_id} kusa={kusa}')
        await send_msg2(event, outputStr)
        await savefile()
    await matcher.finish()


@scheduler.scheduled_job('cron', hour=0)
async def update_loan():
    for uid in user_data:
        data = user_data[uid]
        if data['loan'] > 0:
            data['loan'] = int(data['loan'] * 1.01)
    await savefile()


@bank_kusa_query.handle()
async def handle(matcher: Matcher, event: MessageEvent):
    tot = 0
    rank = []
    for uid in user_data:
        if user_data[uid]['kusa'] > 0:
            tot += user_data[uid]['kusa']
            rank.append((user_data[uid]['kusa'], uid))
    outputStr = f"总存款为{tot}: "
    rank.sort(reverse=True)
    num = min(25, len(rank))
    for i in range(num):
        outputStr += f'\n{rank[i][1]} : {rank[i][0]}'
    if len(rank) > 25:
        outputStr += '\n(只展示前25)'
    await send_msg2(event, outputStr)
    await matcher.finish()


@bank_loan_query.handle()
async def handle(matcher: Matcher, event: MessageEvent):
    tot = 0
    rank = []
    for uid in user_data:
        if user_data[uid]['loan'] > 0:
            tot += user_data[uid]['loan']
            rank.append((user_data[uid]['loan'], uid))
    outputStr = f"总欠款为{tot}: "
    rank.sort(reverse=True)
    num = min(25, len(rank))
    for i in range(num):
        outputStr += f'\n{rank[i][1]} : {rank[i][0]}'
    if len(rank) > 25:
        outputStr += '\n(只展示前25)'
    await send_msg2(event, outputStr)
    await matcher.finish()


@bank_query_user.handle()
async def handle(matcher: Matcher, event: MessageEvent, arg: Message = CommandArg()):
    uid: str = arg.extract_plain_text().strip()
    if uid not in user_data:
        await send_msg2(event, f'用户{uid}在草行没有账户')
        await matcher.finish()
    data = user_data[uid]
    outputStr = f'用户{uid}:'
    outputStr += f'\n在草行的存款为{data["kusa"]}草' if data['kusa'] > 0 else '\n在草行没有存款'
    outputStr += f'\n其中，有{data["kusa_new"]}草是新存入的' if data['kusa_new'] > 0 else ''
    outputStr += f'\n上期存款为{data["last_kusa"]}草'
    outputStr += f'\n在草行的欠款为{data["loan"]}草' if data['loan'] > 0 else '\n在草行没有欠款'
    outputStr += f'\n已预约取出{data["kusa_out"]}草' if data['kusa_out'] > 0 else ''
    await send_msg2(event, outputStr)
    await matcher.finish()


@bank_kusa_update.handle()
async def handle(matcher: Matcher, event: MessageEvent):
    # await update_kusa()
    # await send_msg2(event, "周期结算结束")
    await send_msg2(event, "不能使用")
    await matcher.finish()


@bank_loan_add.handle()
async def handle(matcher: Matcher, event: MessageEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    uid = args[0]
    kusa = int(args[1])
    await init_user(uid)
    user_data[uid]['loan'] += kusa
    await savefile()
    await send_msg2(event, f'给用户{uid}记账{kusa}成功')
    await matcher.finish()


@bank_loan_del.handle()
async def handle(matcher: Matcher, event: MessageEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    uid = args[0]
    kusa = int(args[1])
    await init_user(uid)
    user_data[uid]['loan'] -= kusa
    if user_data[uid]['loan'] < 0:
        user_data[uid]['loan'] = 0
    await savefile()
    await send_msg2(event, f'给用户{uid}销账{kusa}成功')
    await matcher.finish()


@bank_freeze.handle()
async def handle(matcher: Matcher, event: MessageEvent):
    if freeze_flag > 0:
        outputStr = '解除草行维护状态'
        await bank_unfreeze()
    else:
        outputStr = '开始草行维护'
        await bank_freeze()
    await send_msg2(event, outputStr)
    await matcher.finish()


async def get_user_ratio(bot: Bot, user_id: int) -> float:
    uid = str(user_id)
    if uid in bot.config.superusers:
        return 1.0
    await init_user(uid)
    return user_data[uid]['last_kusa'] / bank_data['total_storage']


async def get_user_true_kusa(bot: Bot, user_id: int) -> int:
    uid = str(user_id)
    if uid in bot.config.superusers:
        return bank_data['total_kusa']
    await init_user(uid)
    return user_data[uid]['kusa'] - user_data[uid]['kusa_new']


async def set_finance(data: list):
    global investigate_list
    bank_data['finance'] = data
    investigate_list.clear()
    await savefile()


async def get_finance() -> int:
    return bank_data['finance'][0] + bank_data['finance'][1] + bank_data['finance'][2] + bank_data['finance'][3]


async def bank_freeze():
    global freeze_flag
    freeze_flag += 1


async def bank_unfreeze():
    global freeze_flag
    if freeze_flag > 0:
        freeze_flag -= 1


async def get_bank_divvy():
    return bank_data['divvy'], bank_data['divvy_total']


async def set_bank_kusa(kusa: int):
    bank_data['total_kusa'] = kusa
    await savefile()


@cnt_divvy.handle()
async def handle(matcher: Matcher):
    await bank_freeze()
    async with lock_divvy:
        bank_data['divvy_total'] = 0
        m = await get_finance()
        n = bank_data['total_kusa']
        if m / n > 0.1:
            bank_data['divvy_total'] = int(0.1 * m * bank_data['total_storage'] / bank_data['total_kusa'])
        bank_data['divvy'] = bank_data['divvy_total']
        bank_data['divvy_user_list'].clear()
        await savefile()
    await matcher.finish()


@bank_ratio.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    await send_msg2(event, """
贷草利率计算方式: 
日利率1%，利滚利，每天0点结算，用途不限
贷草并非草行收入来源，利率为市场价

存草利率计算方式:
周期(每3天)利率0.6%
新存入的草从下下次G周期结算开始计算（强调：下下次），每次结算自动更新存款，也是利滚利形式
该模式下折合年化利率约107%
""".strip())
    await matcher.finish()

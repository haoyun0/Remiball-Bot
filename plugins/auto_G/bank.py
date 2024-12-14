import asyncio
import json
import math
import random
import re
from datetime import datetime, timedelta
from typing import Annotated, Union, Callable, Awaitable

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
notice_id = plugin_config.bot_g1
bot_bank = plugin_config.bot_main
bot_G3 = plugin_config.bot_g3

freeze_flag = 0
lock_divvy = asyncio.Lock()
investigate_list = {}
factory_num = 8

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
user_get_factory = on_command('草借厂',
                              rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
user_return_factory = on_command('草还厂',
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
bank_loan_free = on_command('草免息',
                            rule=isInBotList([bot_bank]), permission=SUPERUSER)
bank_admin_divvy = on_command('草分红',
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
            'kusa_envelope': 0,
            'factory_place': 0,
            'scout': 0,
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
    'loan_free': 0,
    'last_kusa': 0,
    'divvy': {
        '贷款利息': 0,
        '流动厂': 0,
        'G市': 0
    }
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
    if bank_data["kusa_envelope"] > 0:
        outputStr = f'草行将于明天中午11:35发出{bank_data["kusa_envelope"]}草的草包，记得来领取哦^ ^\n'
        await send_msg(bot_bank, group_id=ceg_group_id, message=outputStr)
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
                 expire_time=datetime.now() + timedelta(seconds=30), temp=True, handlers=[handle_receive])
    await send_msg2(event,
                    f'请将存款用你的账号发给bot，不低于1w草，限时30s，每存一笔需要重新触发指令\n\n!草转让 qq={event.self_id} kusa=')
    await matcher.finish()


@bank_user_take.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    async with lock_send_kusa:
        uid = event.get_user_id()
        await init_user(uid)
        arg: str = arg.extract_plain_text().strip()
        mul = 1
        if arg[-1] == 'm':
            arg = arg[:-1]
            mul = 1000000
        if not arg.isnumeric() or int(arg) <= 0:
            await send_msg2(event, '请在指令参数输入要立即取款的数额')
            await matcher.finish()
        num = int(arg) * mul
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
        if s[2] - s[0] > s[3] - s[1]:
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
                 expire_time=datetime.now() + timedelta(seconds=30), temp=True, handlers=[handle_receive3])
    await send_msg2(event, f'审批额度需要交10000草手续费，请在30s内复制下述指令交手续费\n'
                           f'\n!草转让 qq={event.self_id} kusa=10000')
    await matcher.finish()


@bank_user_loan.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    async with lock_send_kusa:
        uid = event.get_user_id()
        await init_user(uid)
        if user_data[uid]['loan_free'] > 0:
            await send_msg2(event, '享有免息者不能自助借款，需要请联系工作人员')
            await matcher.finish()
        if user_data[uid]['loan_amount'] == 0:
            await send_msg2(event, '请先使用草审批指令审核贷草额度')
            await matcher.finish()
        arg: str = arg.extract_plain_text().strip()
        if not arg:
            await send_msg2(event, '请在指令参数输入要贷草的数额\n利率请使用/草利率 指令查看')
            await matcher.finish()
        mul = 1
        if arg[-1] == 'm':
            arg = arg[:-1]
            mul = 1000000
        if not arg.isnumeric() or int(arg) <= 0:
            await send_msg2(event, '请在指令参数输入要贷草的数额\n利率请使用/草利率 指令查看')
            await matcher.finish()
        num = int(arg) * mul
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
                 expire_time=datetime.now() + timedelta(seconds=30), temp=True, handlers=[handle_receive2])
    await send_msg2(event, f'您在草行的欠款为{user_data[uid]["loan"]}草\n'
                           f'请将准备的欠款用你的账号发给bot，不低于1w草每次，限时30s，每还一笔需要重新触发指令，多还的自动存款'
                           f'\n\n!草转让 qq={event.self_id} kusa=')
    await matcher.finish()


@user_get_factory.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    arg: str = arg.extract_plain_text().strip()
    if arg != '确认':
        await send_msg2(event, "请务必认真阅读以下借流动厂需知\n"
                               f"流动厂为生草系统特殊贡献者所有，目前归银行统一自动化管理，目前有{factory_num}个流动厂\n"
                               "请在借厂前先建好自己所需要的厂，以免影响计算\n"
                               "借厂则默认使用流动厂建厂，将会在还厂时根据你最后的草精炼厂数计算花费\n"
                               "收费比例为原先建厂需要的费用乘(0.1 + 0.05 * 建完后草精炼厂数求余7)\n"
                               "\n如果已经确认读完上述需知，请输入'/草借厂 确认'来开始借厂流程")
        await matcher.finish()
    if bank_data['factory_place'] == 0:
        uid = event.get_user_id()
        await init_user(uid)
        _ = on_regex(rf"^.*?\({event.user_id}\)转让了10000个草给你！",
                     rule=PRIVATE() & isInBotList([bot_bank]), permission=isInUserList([chu_id]), block=True,
                     expire_time=datetime.now() + timedelta(seconds=30), temp=True, handlers=[handle_receive4])
        await send_msg2(event, f'借流动厂需要额外交10000草手续费，请在30s内复制下述指令交手续费\n'
                               f'\n!草转让 qq={event.self_id} kusa=10000')
    else:
        await send_msg2(event, f"流动厂已经借出给{bank_data['factory_place']}")
    await matcher.finish()


@user_return_factory.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    if bank_data['factory_place'] != event.user_id:
        await send_msg2(event, "你不需要还厂")
        await matcher.finish()
    arg: str = arg.extract_plain_text().strip()
    if not arg.isdigit() or len(arg) == 0 or int(arg) <= 4 or int(arg) > 10:
        await send_msg2(event, "请在指令参数中输入您的信息员等级+生草工厂自动工艺等级\n"
                               "例如信息员lv7，买了333的生草工厂自动工艺I，则输入/草还厂 8\n"
                               "!仓库可看自己信息员等级，!能力可以看到自动工艺等级\n"
                               "请注意诚信，否则可能上银行失信名单")
        await matcher.finish()
    await scout_storage(bot_bank, storage_handle, state={'uid': event.get_user_id(), 'level': int(arg)})


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
                          arg: str = EventPlainText()):
    r = re.search(r"^.*?\((\d+)\)转让了(\d+)个草给你！", arg)
    uid = r.group(1)
    await init_user(uid)
    await scout_storage(uid, other_storage_handle, state={'user_id': uid})
    await matcher.finish()


async def handle_receive4(matcher: Annotated[Matcher, Depends(handleOnlyOnce, use_cache=False)],
                          bot: Bot, arg: str = EventPlainText()):
    r = re.search(r"^.*?\((\d+)\)转让了(\d+)个草给你！", arg)
    uid = r.group(1)
    await init_user(uid)
    await send_msg(bot, user_id=chu_id, message=f'!购买 侦察凭证 1')
    bank_data['factory_place'] = int(uid)
    await savefile()
    await send_msg(bot, user_id=chu_id, message=f'!转让 qq={uid} 流动生草工厂 {factory_num}')
    await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]厂已借出，可以直接使用!购买 草精炼厂建厂了，建完后请复制以下指令归还，'
                                                       f'并在归还后使用"/草还厂"指令来结算费用\n'
                                                       f'\n!转让 qq={bot.self_id} 流动生草工厂 {factory_num}')
    await send_msg(bot_G3, user_id=notice_id, message=f'用户{uid}借走了流动生草工厂')
    await matcher.finish()


async def other_storage_handle(matcher: Matcher, state: T_State, arg: str = EventPlainText()):
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
    await send_msg(bot_bank, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]经过审批，您在草行的借草额度为{result}草')
    await matcher.finish()


async def storage_handle(matcher: Matcher, bot: Bot, state: T_State, arg: str = EventPlainText()):
    uid = state['uid']
    r = re.search(r", 流动生草工厂 \* (\d+)", arg)
    if r is not None:
        num = int(r.group(1))
        if num >= factory_num:
            bank_data['factory_place'] = 0
            await savefile()
            await scout_storage(uid, other_storage_handle2, state={'uid': uid, 'level': state['level']})
            await matcher.finish()
    await send_msg(bot, group_id=ceg_group_id, message=f"[CQ:at,qq={uid}]尚未收到流动生草工厂")
    await matcher.finish()


async def other_storage_handle2(matcher: Matcher, state: T_State, arg: str = EventPlainText()):
    uid = state['uid']
    e = state['level']
    r = re.search(r", 生草工厂 \* (\d+)", arg)
    factoryBefore = int(r.group(1)) if r is not None else 0
    factoryAfter = factoryBefore + factory_num
    base = 1 + .5 * math.exp(-0.255 * e)
    ans = math.floor((base ** factoryBefore) * ((base ** (factoryAfter - factoryBefore)) - 1) / (base - 1))

    r = re.search(r", 草精炼厂 \* (\d+)", arg)
    factory = int(r.group(1)) if r is not None else 0
    factory2 = factory % 7
    ans = int(ans * 1000 * (0.1 + factory2 * 0.05))
    await send_msg(bot_bank, group_id=ceg_group_id,
                   message=f'[CQ:at,qq={uid}]还厂成功，本次费用为{ans}，已计入草行欠款，请用还款指令支付。')
    if uid in plugin_config.factory_owner or uid == str(plugin_config.stone_id):
        ans = 0
    user_data[uid]['loan'] += ans
    await send_msg(bot_G3, user_id=notice_id, message=f'用户{uid}还回了流动生草工厂，费用为{ans}\n'
                                                      f'原草厂{factoryBefore}, 精炼厂{factory}, lv{e}')
    for uid in plugin_config.factory_owner:
        user_data[uid]['divvy']['流动厂'] += int(ans / (len(plugin_config.factory_owner) + 1))
    await savefile()
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
        n = math.ceil(state['kusa'] * 0.01)
        await handout_divvy('贷款利息', int(n * 0.6))
        user_data[uid]['loan'] += state['kusa'] + n
        await savefile()
        await send_msg(bot, group_id=ceg_group_id, message=f"[CQ:at,qq={uid}]借草{state['kusa']}成功")
    else:
        await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]银行流动草不足，若要贷草请联系扫地机')
    await matcher.finish()


@get_divvy.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent):
    async with lock_divvy:
        uid = event.get_user_id()
        await init_user(uid)
        kusa = 0
        outputStr = f"尊贵的股东{uid}:"
        for dtype in user_data[uid]['divvy']:
            if user_data[uid]['divvy'][dtype] > 0:
                kusa += user_data[uid]['divvy'][dtype]
                outputStr += f'\n您获得了{user_data[uid]["divvy"][dtype]}草的{dtype}分红'
                user_data[uid]['divvy'][dtype] = 0

        if kusa == 0:
            await send_msg2(event, '当前没有可领取的分红')
            await matcher.finish()

        await send_msg(bot, user_id=chu_id, message=f'!草转让 qq={event.user_id} kusa={kusa}')
        await send_msg2(event, outputStr)
        await savefile()
    await matcher.finish()


@scheduler.scheduled_job('cron', hour=0)
async def update_loan():
    n = 0
    for uid in user_data:
        data = user_data[uid]
        if data['loan'] > 0:
            if data['loan_free'] > 0:
                data['loan_free'] -= 1
                continue
            n += math.ceil(data['loan'] * 0.01)
            data['loan'] = math.ceil(data['loan'] * 1.01)
    await handout_divvy('贷款利息', int(n * 0.6))
    await savefile()


@scheduler.scheduled_job('cron', hour=11, minute=35)
async def update_loan():
    if bank_data['kusa_envelope'] > 0:
        await send_msg(bot_bank, user_id=chu_id, message=f'!草转让 qq={bot_G3} kusa={bank_data["kusa_envelope"]}')
        await send_msg(bot_G3, group_id=ceg_group_id, message="/发草包 15")
        await asyncio.sleep(3)
        await send_msg(bot_G3, user_id=chu_id, message=f'!草转让 qq={bot_bank} kusa={bank_data["kusa_envelope"]}')
        bank_data['kusa_envelope'] = 0
        await savefile()


@scheduler.scheduled_job('cron', minute='1,11,21,31,41,51')
async def check_factory():
    if bank_data['factory_place'] != 0:
        await send_msg(bot_bank, group_id=ceg_group_id,
                       message=f"[CQ:at,qq={bank_data['factory_place']}]自动提示:\n"
                               f"请记得还流动厂，如已经还厂，请使用'/草还厂'指令，并仔细阅读其提示")


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
            rank.append((user_data[uid]['loan'], uid, user_data[uid]['loan_free']))
    outputStr = f"总欠款为{tot}: "
    rank.sort(reverse=True)
    num = min(25, len(rank))
    for i in range(num):
        free = f"({rank[i][2]})" if rank[i][2] > 0 else ""
        outputStr += f'\n{rank[i][1]}{free} : {rank[i][0]}'
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
    outputStr += f'\n在草行有{data["loan_free"]}次免息次数' if data['loan_free'] > 0 else ''
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


@bank_loan_free.handle()
async def handle(matcher: Matcher, event: MessageEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    uid = args[0]
    times = int(args[1])
    await init_user(uid)
    user_data[uid]['loan_free'] += times
    await savefile()
    await send_msg2(event, f'给用户{uid}记免息{times}次成功')
    await matcher.finish()


@bank_admin_divvy.handle()
async def handle(matcher: Matcher, event: MessageEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    await handout_divvy(args[0], int(args[1]))
    await send_msg2(event, f'分发{args[0]}分红{args[1]}草成功')
    await matcher.finish()


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


async def bank_freeze():
    global freeze_flag
    freeze_flag += 1


async def bank_unfreeze():
    global freeze_flag
    if freeze_flag > 0:
        freeze_flag -= 1


async def get_bank_divvy():
    ans = bank_data["kusa_envelope"]
    for uid in user_data:
        for dtype in user_data[uid]['divvy']:
            ans += user_data[uid]['divvy'][dtype]
    return ans


async def set_bank_kusa(kusa: int):
    bank_data['total_kusa'] = kusa
    await savefile()


async def set_bank_scout(num: int):
    bank_data['scout'] = num


async def scout_storage(uid: Union[str, int], func: Callable[..., Awaitable], state=None):
    if uid == 0 or uid == '0':
        return
    if int(uid) not in [plugin_config.bot_g0, plugin_config.bot_g1, plugin_config.bot_g2, plugin_config.bot_g3]:
        bot = bot_bank
        msg = f'!仓库 qq={uid}'
        if bank_data['scout'] <= 100:
            bank_data['scout'] += 100
            await send_msg(bot_bank, user_id=chu_id, message=f'!购买 侦察凭证 100')
        bank_data['scout'] -= 1
        await savefile()
    else:
        bot = int(uid)
        msg = '!仓库'

    _ = on_regex(r'当前拥有草: \d+\n',
                 rule=PRIVATE() & isInBotList([bot]), permission=isInUserList([chu_id]), block=True,
                 temp=True, handlers=[func],
                 state=state, expire_time=datetime.now() + timedelta(seconds=9))
    await send_msg(bot, user_id=chu_id, message=msg)


@cnt_divvy.handle()
async def handle(matcher: Matcher):
    await bank_freeze()
    async with (lock_divvy):
        fn = bank_data['finance'][0] + bank_data['finance'][1] + bank_data['finance'][2] + bank_data['finance'][3]
        bank_data['finance'] = [0, 0, 0, 0]
        if fn / bank_data['total_kusa'] > 0.1:
            m0 = int(0.1 * fn)
            m1 = int(m0 * bank_data['total_storage'] / bank_data['total_kusa'])
            m2 = int((m0 - m1) / 2)

            bank_data['kusa_envelope'] = m2
            await send_msg(bot_bank, group_id=ceg_group_id, message=f'草行为用户发出了{m1 + m2}草的G市分红')
            await handout_divvy('G市', m1 + m2)

            await savefile()
    await send_msg(bot_bank, group_id=plugin_config.group_id_test, message='/集资')
    await asyncio.sleep(10)
    await send_msg(bot_bank, group_id=ceg_group_id, message=f'!仓库 qq={chu_id}')
    await matcher.finish()


async def handout_divvy(divvy_type: str, total_kusa: int):
    if total_kusa == 0:
        return
    n = 0
    for uid in user_data:
        n += user_data[uid]['last_kusa']
    for uid in user_data:
        r = user_data[uid]['last_kusa'] / n
        user_data[uid]['divvy'][divvy_type] += int(total_kusa * r)


@bank_ratio.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    await send_msg2(event, """
贷草利率计算方式: 
日利率1%，利滚利，每天0点结算，用途不限
贷草并非草行收入来源，利率为市场价
借出时会立刻结算一次利息
(利息的六成将分红给存款用户)

存草利率计算方式:
周期(每3天)利率0.6%
新存入的草从下下次G周期结算开始计算（强调：下下次），每次结算自动更新存款，也是利滚利形式
该模式下折合年化利率约107%

超过额度的借款可以找扫地机谈
用于基建的萌新可获得一定时间的免息
""".strip())
    await matcher.finish()

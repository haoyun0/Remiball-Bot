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
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")

chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
admin_list = [323690346, 847360401, 3584213919, 3345744507]
bot_bank = 3584213919

lock_divvy = asyncio.Lock()
investigate_list = {}

# 用户指令
bank_help = on_command('草行',
                       rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))
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
                             rule=isInBotList([bot_bank]) & isInUserList(admin_list))
bank_loan_query = on_command('查看草贷款',
                             rule=isInBotList([bot_bank]) & isInUserList(admin_list))
bank_query_user = on_command('查看草账户',
                             rule=isInBotList([bot_bank]) & isInUserList(admin_list))
bank_loan_add = on_command('草记账',
                           rule=isInBotList([bot_bank]) & isInUserList(admin_list))
bank_loan_del = on_command('草销账',
                           rule=isInBotList([bot_bank]) & isInUserList(admin_list))
bank_kusa_update = on_command('草结算',
                              rule=isInBotList([bot_bank]) & isInUserList(admin_list))
# 并非指令
cnt_divvy = on_regex('^新的G周期开始了！上个周期的G已经自动兑换为草。$',
                     rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]) & isInUserList([chu_id]))

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
        bank_data['total_storage'] += data['kusa']
    await savefile()


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


@bank_user_store.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    uid = event.get_user_id()
    await init_user(uid)
    _ = on_regex(rf"^.*?\({event.user_id}\)转让了\d+个草给你！",
                 rule=PRIVATE() & isInBotList([bot_bank]) & isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive])
    await send_msg2(event,
                    f'请将存款用你的账号发给bot，不低于1w草，限时60s，每存一笔需要重新触发指令\n\n!草转让 qq={event.self_id} kusa=')
    await matcher.finish()


@bank_user_take.handle()
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
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
                 rule=PRIVATE() & isInBotList([bot_bank]) & isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=5), temp=True, handlers=[handle_give_kusa],
                 state={'uid': uid, 'kusa': num})
    await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={uid} kusa={num}")
    await matcher.finish()


@bank_user_take_more.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
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
    await matcher.finish()


@bank_earn.handle()
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


@bank_user_judge.handle()
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
                 rule=PRIVATE() & isInBotList([bot_bank]) & isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive3])
    await send_msg2(event, f'审批额度需要交10000草手续费，请复制下述指令交手续费\n'
                           f'\n!草转让 qq={event.self_id} kusa=10000')
    await matcher.finish()


@bank_user_loan.handle()
async def handle(matcher: Matcher, bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
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
                 rule=PRIVATE() & isInBotList([bot_bank]) & isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=5), temp=True, handlers=[handle_give_loan],
                 state={'uid': uid, 'kusa': num})
    await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={uid} kusa={num}")
    await matcher.finish()


@bank_user_repayment.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    uid = event.get_user_id()
    await init_user(uid)
    if user_data[uid]['loan'] == 0:
        await send_msg2(event, '您不需要还款')
        await matcher.finish()
    _ = on_regex(rf"^.*?\({event.user_id}\)转让了\d+个草给你！",
                 rule=PRIVATE() & isInBotList([bot_bank]) & isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive2])
    await send_msg2(event, f'您在草行的欠款为{user_data[uid]["loan"]}草\n'
                           f'请将准备的欠款用你的账号发给bot，不低于1w草每次，限时60s，每还一笔需要重新触发指令，多还的自动存款'
                           f'\n\n!草转让 qq={event.self_id} kusa=')
    await matcher.finish()


async def handle_receive(matcher: Matcher, event: PrivateMessageEvent, bot: Bot, arg: str = EventPlainText()):
    # ({userId})转让了{transferKusa}个草给你！
    if not isReceiveValid(event.message_id):
        await matcher.finish()
    r = re.search(r"^.*?\((\d+)\)转让了(\d+)个草给你！", arg)
    uid, kusa_num = r.group(1), int(r.group(2))
    await init_user(uid)
    user_data[uid]['kusa'] += kusa_num
    user_data[uid]['kusa_new'] += kusa_num
    await savefile()
    await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]成功存入{kusa_num}草')
    await matcher.finish()


async def handle_receive2(matcher: Matcher, event: PrivateMessageEvent, bot: Bot, arg: str = EventPlainText()):
    if not isReceiveValid(event.message_id):
        await matcher.finish()
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


async def handle_receive3(matcher: Matcher, event: PrivateMessageEvent, bot: Bot, arg: str = EventPlainText()):
    if not isReceiveValid(event.message_id):
        await matcher.finish()
    r = re.search(r"^.*?\((\d+)\)转让了(\d+)个草给你！", arg)
    uid = r.group(1)
    await init_user(uid)
    await send_msg(bot, user_id=chu_id, message=f'!购买 侦察凭证 1')
    _ = on_regex(r'当前拥有草: \d+\n', rule=PRIVATE() & isInUserList([chu_id]),
                 temp=True, handlers=[other_storage_handle],
                 state={'user_id': uid}, expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(bot, user_id=chu_id, message=f'!仓库 qq={uid}')
    await matcher.finish()


async def other_storage_handle(matcher: Matcher, bot: Bot, state: T_State, arg: str = EventPlainText()):
    uid = state['user_id']
    if '草精炼厂' in arg:
        tmp = arg.index('草精炼厂 * ') + 7
        factory = 0
        while arg[tmp].isdigit():
            factory = factory * 10 + int(arg[tmp])
            tmp += 1
        if factory >= 35:
            result = 1000000000
        elif factory >= 28:
            result = 400000000
        elif factory >= 21:
            result = 200000000
        elif factory >= 14:
            result = 100000000
        elif factory >= 7:
            result = 50000000
        else:
            result = 0
    else:
        result = 0
    user_data[uid]['loan_amount'] = result
    await savefile()
    if result > 0:
        await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]经过审批，您在草行的借草额度为{result}草')
    else:
        await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]萌新先好好发展，不批准借草')
    await matcher.finish()


async def handle_give_kusa(matcher: Matcher, event: PrivateMessageEvent, bot: Bot, state: T_State,
                           arg: str = EventPlainText()):
    if not isReceiveValid(event.message_id):
        await matcher.finish()
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


async def handle_give_loan(matcher: Matcher, event: PrivateMessageEvent, bot: Bot, state: T_State,
                           arg: str = EventPlainText()):
    if not isReceiveValid(event.message_id):
        await matcher.finish()
    uid = state['uid']
    if '转让成功' in arg:
        user_data[uid]['loan'] += int(state['kusa'] * 1.01)
        await savefile()
        await send_msg(bot, group_id=ceg_group_id, message=f"[CQ:at,qq={uid}]借草{state['kusa']}成功")
    else:
        await send_msg(bot, group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]银行流动草不足，若要贷草请联系扫地机')
    await matcher.finish()


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
        if event.user_id in bank_data['divvy_user_list']:
            await send_msg2(event, '你已经领过上期分红^ ^')
            await matcher.finish()

        bank_data['divvy_user_list'].append(event.user_id)
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
    outputStr += f'\n在草行的欠款为{data["loan"]}草' if data['loan'] > 0 else '\n在草行没有欠款'
    outputStr += f'\n已预约取出{data["kusa_out"]}草' if data['kusa_out'] > 0 else ''
    await send_msg2(event, outputStr)
    await matcher.finish()


@bank_kusa_update.handle()
async def handle(matcher: Matcher, event: MessageEvent):
    await update_kusa()
    await send_msg2(event, "周期结算结束")
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


async def get_user_ratio(user_id: int) -> float:
    if user_id in admin_list:
        return 1.0
    uid = str(user_id)
    await init_user(uid)
    return user_data[uid]['last_kusa'] / bank_data['total_storage']


async def get_user_num() -> int:
    ans = 0
    for uid in user_data:
        if user_data[uid]['kusa'] - user_data[uid]['kusa_new'] > 0:
            ans += 1
    return ans


async def set_finance(data: list):
    global investigate_list
    bank_data['finance'] = data
    investigate_list.clear()
    await savefile()


async def get_finance() -> int:
    return bank_data['finance'][0] + bank_data['finance'][1] + bank_data['finance'][2] + bank_data['finance'][3]


@cnt_divvy.handle()
async def handle(matcher: Matcher, bot: Bot):
    async with lock_divvy:
        bank_data['divvy_total'] = 0
        m = await get_finance()
        n = bank_data['total_storage']
        if m / n > 0.1:
            bank_data['divvy_total'] = int(0.1 * m)
            await send_msg(bot, group_id=ceg_group_id, message=f'草行发出了{bank_data["divvy_total"]}草的分红，记得来草行领取哦^ ^')
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


@bank_help.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    msg = """
草行3.0 重生
指令列表如下，前面加/
草行 : 查看该帮助
草利率 : 查看存草和贷草利率及计算方式
草盈亏 : 查看本期草行投资盈亏
草账户 : 查看自己的账户信息
草存入 : 开始存草流程
草取出 num: 立即取出草（如果草行还有流动草的话）
草预约取出 num: 大额取出需要预约，在下次G市重置时取出
草审批 : 开始审批借草额度
草借款 num : 自助借草，会立即产生一次利息
草还款 : 开始还草流程
G帮助 : 帮帮草行炒G
分红 : 获取草行分红
""".strip()
    if event.user_id in admin_list:
        msg += '\n\n'
        msg += """
管理员指令如下
查看草存款 : 查看所有用户存款
查看草贷款 : 查看所有用户贷款
查看草账户 qq: 查看某用户的账户信息
草记账 qq num: 给用户贷款记账
草销账 qq num: 给用户贷款销账
""".strip()
    await send_msg2(event, msg)
    await matcher.finish()

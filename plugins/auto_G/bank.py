import asyncio
import json
import random
from datetime import datetime, timedelta

from nonebot import require, get_bot, on_command, on_regex
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventPlainText, T_State
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    PrivateMessageEvent,
    Message,
    Bot
)
from .myrule import isInUserList, Message_select_group, isInBotList, PRIVATE
from ..kusa_helper.xiaohao import isXiaoHao
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")

chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
admin_list = [323690346, 847360401, 3584213919, 3345744507]
bank_bot = 3584213919
G_bot = 3345744507
GBot_list = [847360401, 3584213919, 3345744507]
conclude_data = {}
investigate_list = []
loan_amount = {}

# 用户指令
bank_help = on_command('草行',
                       rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_ratio = on_command('草利率',
                        rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_earn = on_command('草盈亏',
                       rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_user_data = on_command('草账户',
                            rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_user_store = on_command('草存入',
                             rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_user_take = on_command('草取出',
                            rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_user_take_more = on_command('草大额取出', aliases={'草预约取出'},
                                 rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_user_judge = on_command('草审批',
                             rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_user_loan = on_command('草借款',
                            rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
bank_user_repayment = on_command('草还款',
                                 rule=Message_select_group(ceg_group_id) & isInBotList([bank_bot]))
# 管理员指令
bank_set_kusa = on_command('流动草设置',
                           rule=isInBotList([bank_bot]) & isInUserList(admin_list))
bank_query_kusa_free = on_command('流动草查询',
                                  rule=isInBotList([bank_bot]) & isInUserList(admin_list))
bank_kusa_query = on_command('查看草存款',
                             rule=isInBotList([bank_bot]) & isInUserList(admin_list))
bank_loan_query = on_command('查看草贷款',
                             rule=isInBotList([bank_bot]) & isInUserList(admin_list))
bank_query_user = on_command('查看草账户',
                             rule=isInBotList([bank_bot]) & isInUserList(admin_list))
bank_loan_add = on_command('草记账',
                           rule=isInBotList([bank_bot]) & isInUserList(admin_list))
bank_loan_del = on_command('草销账',
                           rule=isInBotList([bank_bot]) & isInUserList(admin_list))
bank_kusa_update = on_command('草结算',
                              rule=isInBotList([bank_bot]) & isInUserList(admin_list))

try:
    with open(r'C:/Data/bank.txt', 'r', encoding='utf-8') as f:
        data_raw = json.loads(f.read())
        user_data = data_raw['user']
        bank_data = data_raw['bank']
except:
    data_raw = {
        'user': {},
        'bank': {
            'kusa': 0
        }
    }
    user_data = data_raw['user']
    bank_data = data_raw['bank']
block_msg = []
lock_rename = asyncio.Lock()
lock2 = asyncio.Lock()


async def savefile():
    with open(r'C:/Data/bank.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(data_raw))


async def init_user(uid: str):
    if uid not in user_data:
        user_data[uid] = {
            'kusa': 0,
            'kusa_new': 0,
            'loan': 0,
            'kusa_out': 0
        }


async def set_kusa(kusa: int):
    bank_data['kusa'] = kusa
    await savefile()


async def update_kusa():
    for uid in user_data:
        data = user_data[uid]
        # 产生利息
        num = data['kusa'] - data['kusa_new']
        if num > 0:
            data['kusa'] += int(num * 0.006)
        data['kusa_new'] = 0
        # 预约取出
        if data['kusa_out'] > 0:
            num = data['kusa_out'] if data['kusa_out'] < data['kusa'] else data['kusa']
            data['kusa_out'] = 0
            if num > 0:
                bot: Bot = get_bot(str(bank_bot))
                bot2: Bot = get_bot(str(G_bot))
                await asyncio.sleep(1)
                await bot2.send_private_msg(user_id=chu_id, message=f'!草转让 qq={uid} kusa={num}')
                await bot.send_group_msg(group_id=ceg_group_id, message=f'[CQ:at,qq={uid}] 您预约的{num}草已取出')
                data['kusa'] -= num
    await savefile()
    await asyncio.sleep(1)


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
    await matcher.finish(outputStr)


@bank_user_store.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    uid = event.get_user_id()
    await init_user(uid)
    _ = on_regex(rf"\({event.user_id}\)转让了\d+个草给你！",
                 rule=PRIVATE() & isInBotList([bank_bot]) & isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive])
    await matcher.finish(
        f'请将存款用你的账号发给bot，不低于1w草，限时60s，每存一笔需要重新触发指令\n\n!草转让 qq={event.self_id} kusa=')


@bank_user_take.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    uid = event.get_user_id()
    await init_user(uid)
    arg: str = arg.extract_plain_text().strip()
    if not arg.isnumeric():
        await matcher.finish('请在指令参数输入要立即取款的数额')
    num = int(arg)
    if num > user_data[uid]['kusa']:
        await matcher.finish('余额不足')
    if num > 0:
        if num <= bank_data['kusa']:
            bank_data['kusa'] -= num
            user_data[uid]['kusa'] -= num
            user_data[uid]['kusa_new'] = user_data[uid]['kusa_new'] - num if num <= user_data[uid]['kusa_new'] else 0
            if user_data[uid]['kusa_out'] > user_data[uid]['kusa']:
                user_data[uid]['kusa_out'] = user_data[uid]['kusa']
            await savefile()
            bot: Bot = get_bot(str(bank_bot))
            await bot.send_private_msg(user_id=chu_id, message=f"!草转让 qq={uid} kusa={num}")
        else:
            await matcher.finish(f"银行流动草不足，请用大额取款取草")
    await matcher.finish(f"取出{num}草成功")


@bank_user_take_more.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    uid = event.get_user_id()
    await init_user(uid)
    arg: str = arg.extract_plain_text().strip()
    if not arg.isnumeric():
        await matcher.finish('请在指令参数输入要预约取款的数额')
    num = int(arg)
    if num > user_data[uid]['kusa']:
        await matcher.finish('余额不足')
    user_data[uid]['kusa_out'] = num
    await savefile()
    await matcher.finish(f"已将预约取款的数额设置为{num}")


@bank_earn.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    async with lock2:
        if len(conclude_data) >= 4:
            max_earn = max(max(conclude_data[GBot_list[0]], conclude_data[GBot_list[1]]), conclude_data[GBot_list[2]])
            min_earn = min(min(conclude_data[GBot_list[0]], conclude_data[GBot_list[1]]), conclude_data[GBot_list[2]])
            random_earn = random.randint(min_earn, max_earn) + max_earn + min_earn
            real_earn = conclude_data[GBot_list[0]] + conclude_data[GBot_list[1]] + conclude_data[GBot_list[2]]

            if event.user_id not in investigate_list:
                investigate_list.append(event.user_id)
            earn = int((random_earn - real_earn) / (len(investigate_list) * 0.77)) + real_earn
            msg = (f"草行当期投资数额为{round(conclude_data[0] / 100000000)}亿草\n"
                   f"当前盈亏可能为{round(earn / 100000000, 1)}亿草")
            await matcher.finish(msg)
        else:
            for i in GBot_list:
                bot: Bot = get_bot(str(i))
                await bot.send_private_msg(user_id=chu_id, message='!交易总结')
            await matcher.send(f'暂无数据，请几秒后重试#{len(conclude_data)}')
            await asyncio.sleep(3)
            await matcher.finish()


@bank_user_judge.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    arg: str = arg.extract_plain_text().strip()
    uid = event.get_user_id()
    await init_user(uid)
    if isXiaoHao(uid):
        await matcher.finish('小号不允许贷草^ ^')
    if arg == '重审':
        if uid in loan_amount:
            del loan_amount[uid]
    if uid in loan_amount:
        await matcher.finish('已存在额度数据，若要重新审批请在指令参数加入“重审”\n'
                             f'当前额度为{loan_amount[uid]}')
    _ = on_regex(rf"\({event.user_id}\)转让了10000个草给你！",
                 rule=PRIVATE() & isInBotList([bank_bot]) & isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive3],
                 state={"user_id": uid})
    await matcher.finish(
        f'审批额度需要交10000草手续费，请复制下述指令交手续费\n'
        f'\n!草转让 qq={event.self_id} kusa=10000')


@bank_user_loan.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    uid = event.get_user_id()
    await init_user(uid)
    if uid not in loan_amount:
        await matcher.finish('请先使用草审批指令审核贷草额度')
    arg: str = arg.extract_plain_text().strip()
    if not arg.isnumeric():
        await matcher.finish('请在指令参数输入要贷草的数额')
    num = int(arg)
    if num + user_data[uid]['loan'] > loan_amount[uid]:
        await matcher.finish('额度不足，若想借草请联系扫地机')
    if num > 0:
        if num <= bank_data['kusa']:
            bank_data['kusa'] -= num
            user_data[uid]['loan'] += int(num * 1.01)
            await savefile()
            bot: Bot = get_bot(str(bank_bot))
            await bot.send_private_msg(user_id=chu_id, message=f"!草转让 qq={uid} kusa={num}")
        else:
            await matcher.finish(f"银行流动草不足，若要贷草请联系扫地机")
    await matcher.finish(f"借款{num}草成功")


@bank_user_repayment.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    uid = event.get_user_id()
    await init_user(uid)
    if user_data[uid]['loan'] == 0:
        await matcher.finish('您不需要还款')
    _ = on_regex(rf"\({event.user_id}\)转让了\d+个草给你！",
                 rule=PRIVATE() & isInBotList([bank_bot]) & isInUserList([chu_id]), block=True,
                 expire_time=datetime.now() + timedelta(seconds=60), temp=True, handlers=[handle_receive2])
    await matcher.finish(
        f'您在草行的欠款为{user_data[uid]["loan"]}草\n'
        f'请将准备的欠款用你的账号发给bot，不低于1w草每次，限时60s，每还一笔需要重新触发指令，多还的草进存款\n\n!草转让 qq={event.self_id} kusa=')


def get_receive_info(arg: str):
    st = len(arg) - 1
    while arg[st] != '(':
        st -= 1
    ed = arg.index(')', st)
    uid = arg[st + 1: ed]
    kusa_num = int(arg[ed + 4: arg.index('个草给你', ed)])
    return uid, kusa_num


async def handle_receive(matcher: Matcher, event: PrivateMessageEvent, bot: Bot, arg: str = EventPlainText()):
    # ({userId})转让了{transferKusa}个草给你！
    async with lock_rename:
        if event.message_id in block_msg:
            await matcher.finish()
        block_msg.append(event.message_id)
    uid, kusa_num = get_receive_info(arg)
    await init_user(uid)
    user_data[uid]['kusa'] += kusa_num
    user_data[uid]['kusa_new'] += kusa_num
    bank_data['kusa'] += kusa_num
    await savefile()
    await bot.send_group_msg(group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]成功存入{kusa_num}草')
    await matcher.finish()


async def handle_receive2(matcher: Matcher, event: PrivateMessageEvent, bot: Bot, arg: str = EventPlainText()):
    async with lock_rename:
        if event.message_id in block_msg:
            await matcher.finish()
        block_msg.append(event.message_id)
    uid, kusa_num = get_receive_info(arg)
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
    bank_data['kusa'] += kusa_num
    await savefile()
    await bot.send_group_msg(group_id=ceg_group_id, message=outputStr)
    await matcher.finish()


async def handle_receive3(matcher: Matcher, event: PrivateMessageEvent, bot: Bot, state: T_State):
    async with lock_rename:
        if event.message_id in block_msg:
            await matcher.finish()
        block_msg.append(event.message_id)
    uid = state['user_id']
    await init_user(uid)
    await bot.send_private_msg(user_id=chu_id, message=f'!购买 侦察凭证 1')
    await asyncio.sleep(1)
    _ = on_regex(r'当前拥有草: \d+\n', rule=PRIVATE() & isInUserList([chu_id]),
                 temp=True, handlers=[other_storage_handle], state={'user_id': uid})
    await bot.send_private_msg(user_id=chu_id, message=f'!仓库 qq={uid}')
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
    loan_amount[uid] = result
    if result > 0:
        await bot.send_group_msg(group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]经过审批，您在草行的借草额度为{result}草')
    else:
        await bot.send_group_msg(group_id=ceg_group_id, message=f'[CQ:at,qq={uid}]萌新先好好发展，不批准借草')
    await matcher.finish()


@scheduler.scheduled_job('cron', hour=0)
async def update_loan():
    for uid in user_data:
        data = user_data[uid]
        if data['loan'] > 0:
            data['loan'] = int(data['loan'] * 1.01)
    await savefile()


@bank_set_kusa.handle()
async def handle(matcher: Matcher, arg: Message = CommandArg()):
    arg: str = arg.extract_plain_text().strip()
    num = int(arg)
    await set_kusa(num)
    await matcher.finish(f"已将流动草设置为{num}")


@bank_query_kusa_free.handle()
async def handle(matcher: Matcher):
    await matcher.finish(f"草行可用流动草为：{bank_data['kusa']}草")


@bank_kusa_query.handle()
async def handle(matcher: Matcher):
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
    await matcher.finish(outputStr)


@bank_loan_query.handle()
async def handle(matcher: Matcher):
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
    await matcher.finish(outputStr)


@bank_query_user.handle()
async def handle(matcher: Matcher, arg: Message = CommandArg()):
    uid: str = arg.extract_plain_text().strip()
    if uid not in user_data:
        await matcher.finish(f'用户{uid}在草行没有账户')
    data = user_data[uid]
    outputStr = f'用户{uid}:'
    outputStr += f'\n在草行的存款为{data["kusa"]}草' if data['kusa'] > 0 else '\n在草行没有存款'
    outputStr += f'\n其中，有{data["kusa_new"]}草是新存入的' if data['kusa_new'] > 0 else ''
    outputStr += f'\n在草行的欠款为{data["loan"]}草' if data['loan'] > 0 else '\n在草行没有欠款'
    outputStr += f'\n已预约取出{data["kusa_out"]}草' if data['kusa_out'] > 0 else ''
    await matcher.finish(outputStr)


async def set_conclude_data(data: dict):
    global conclude_data, investigate_list
    conclude_list.clear()
    conclude_data = data


@bank_kusa_update.handle()
async def handle(matcher: Matcher):
    await update_kusa()
    await matcher.finish(f"周期结算结束")


@bank_loan_add.handle()
async def handle(matcher: Matcher, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    uid = args[0]
    kusa = int(args[1])
    await init_user(uid)
    user_data[uid]['loan'] += kusa
    await savefile()
    await matcher.finish(f'给用户{uid}记账{kusa}成功')


@bank_loan_del.handle()
async def handle(matcher: Matcher, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    uid = args[0]
    kusa = int(args[1])
    await init_user(uid)
    user_data[uid]['loan'] -= kusa
    if user_data[uid]['loan'] < 0:
        user_data[uid]['loan'] = 0
    await savefile()
    await matcher.finish(f'给用户{uid}销账{kusa}成功')


@bank_ratio.handle()
async def handle(matcher: Matcher):
    await matcher.finish("""
贷草利率计算方式: 
日利率1%，利滚利，每天0点结算，用途不限
贷草并非草行收入来源，利率为市场价

存草利率计算方式:
周期(每3天)利率0.6%
新存入的草从下下次G周期结算开始计算（强调：下下次），每次结算自动更新存款，也是利滚利形式
该模式下折合年化利率约107%
""".strip())


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
""".strip()
    if event.user_id in admin_list:
        msg += '\n\n'
        msg += """
管理员指令如下
流动草设置 num: 设置草行可用流动草
流动草查询 : 查看草行可用流动草
查看草存款 : 查看所有用户存款
查看草贷款 : 查看所有用户贷款
查看草账户 qq: 查看某用户的账户信息
草记账 qq num: 给用户贷款记账
草销账 qq num: 给用户贷款销账
""".strip()
    await matcher.finish(msg)


async def cheat_while_rob():
    pass
    # async def send_kusa_immediately(bot: Bot, uid: int, kusa: int):
    #     await asyncio.sleep(2.5)
    #     await bot.send_private_msg(user_id=chu_id,
    #                                message=f"!草转让 qq={uid} kusa={kusa}")
    #
    # async def send_strange(bot: Bot):
    #     await bot.send_private_msg(user_id=chu_id, message="!购买 侦察凭证 10")
    #     await asyncio.sleep(1)
    #     await bot.send_private_msg(user_id=chu_id, message="!草精排行榜")
    #
    # # 尝试卡出仓
    # try:
    #     bot1: Bot = get_bot(str(admin_list[0]))
    #     bot2: Bot = get_bot(str(admin_list[1]))
    #     bot3: Bot = get_bot(str(admin_list[2]))
    #     bot4: Bot = get_bot(str(admin_list[3]))
    #     # await asyncio.sleep(1)
    #     # await bot1.send_private_msg(user_id=chu_id, message="偷")
    #     # num = bank_data['kusa']
    #     # await asyncio.gather(send_strange(bot1),
    #     #                      send_kusa_immediately(bot2, admin_list[2], 1),
    #     #                      send_kusa_immediately(bot3, admin_list[0], num),
    #     #                      send_kusa_immediately(bot4, admin_list[2], 1)
    #     #                      )
    #     # await asyncio.sleep(5)
    #     # await asyncio.gather(send_strange(bot3),
    #     #                      send_kusa_immediately(bot2, admin_list[0], 1),
    #     #                      send_kusa_immediately(bot1, admin_list[2], num),
    #     #                      send_kusa_immediately(bot4, admin_list[0], 1)
    #     #                      )
    # except:
    #     pass

import asyncio
from datetime import datetime, timedelta
import random
import json

from nonebot import on_regex, on_command, require, get_bot
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent
)
from ..params.message_api import send_msg, send_msg2
from ..params.rule import isInUserList, Message_select_group, isInBotList, GROUP
from .kusa_group import rename_to_other, rename_to_itself
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")

chu_id = 3056318700
bot_main = 3345744507
ceg_group_id = 738721109
test_group_id = 278660330
admin_list = [323690346, 847360401, 3584213919, 3345744507]
# file_free_rob = 'D:/data/log/autokusa/free_rob.txt'
file_free_rob = 'C:/data/free_rob.txt'
rob_start = on_regex(r'^喜报\n(.*?玩家.*?使用 .*?草.*? 获得了\d+个草之精华！大家快来围殴他吧！'
                     r'|魔法少女纯酱为生.*?草.*?达成.连的玩家.*?召唤了额外的\d+草之精华喵)',
                     rule=Message_select_group(ceg_group_id) & isInUserList([chu_id]) & isInBotList([bot_main]))
rob_free = on_command('免费礼炮', rule=Message_select_group(ceg_group_id) & isInBotList([bot_main]))
rob_test = on_command('围殴测试', rule=GROUP() & isInBotList([bot_main]) & isInUserList(admin_list))
rob_count = on_regex(r'围殴.*?成功！你获得了\d+草！',
                     rule=Message_select_group(ceg_group_id) & isInBotList([bot_main]))
rob_reset_name = on_regex(rf'^本次围殴结束，玩家',
                          rule=Message_select_group(ceg_group_id) & isInUserList([chu_id]))

rob_list = []
# {uid: int, endTime: datetime}
lock2 = asyncio.Lock()
with open(file_free_rob, mode="r", encoding='utf-8') as f:
    data_free = json.loads(f.read())
    qqList = data_free['qqList']
friend_list = []


async def send_private_rob(bot: Bot, message: str):
    cnt = 0
    failed_list = []
    # 免费私聊礼炮
    for uid in qqList:
        if uid in friend_list:
            if await send_msg(bot, user_id=uid, message=message) is None:
                failed_list.append(uid)
    while len(failed_list) > 0:
        cnt += 1
        if cnt > 20:
            await send_msg(bot, group_id=test_group_id, message=f"失败总次数超过20次, 失败名单{failed_list}")
            break
        uid = failed_list[0]
        del failed_list[0]
        if await send_msg(bot, user_id=uid, message=message) is None:
            failed_list.append(uid)


async def refresh_friend_list():
    global friend_list
    friend_list.clear()
    bot2 = get_bot(str(bot_main))
    friend_list_tmp = await bot2.get_friend_list()
    for friend in friend_list_tmp:
        friend_list.append(friend['user_id'])


async def add_rob(uid: int, endTime: datetime, kusa: int, adv: int, kusa_type: str, message: bool = True):
    for data in rob_list:
        if data['kusa'] == kusa and data['adv'] == adv:
            return False
    rob_list.append({
        'uid': uid,
        'endTime': endTime,
        'times': 1,
        'cooldown': 0,
        'warning': True,
        'kusa': kusa,
        'adv': adv,
        'type': kusa_type
    })
    bot2 = get_bot(str(bot_main))
    if uid == 0 and message:
        await bot2.send_group_msg(group_id=test_group_id,
                                  message='检测到他人喜报')

    await refresh_friend_list()
    if message:
        for uid in qqList:
            if uid in friend_list:
                await bot2.send_private_msg(user_id=uid,
                                            message=f"检测到在途喜报({kusa_type})：" + endTime.strftime("%H:%M"))
    return True


@rob_start.handle()
async def handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    if 'Tokens:' in arg:
        await matcher.finish()

    # 免费群聊礼炮
    random.shuffle(qqList)
    msg = "[CQ:face,id=144]一个喜报产生了！[CQ:face,id=144]\n"
    for uid in qqList:
        msg += f"[CQ:at,qq={uid}]"
    msg += "\n（可以找本账号提供免费礼炮服务^_^） "
    await send_msg(bot, group_id=ceg_group_id, message=msg)

    # 获取信息
    rob_type = '未知类型'
    user_name = '未知玩家'
    kusa_type = '未知草种'
    if '大家快来围殴他吧！' in arg:
        rob_type = '质量'
        tmp = arg.index('玩家 ') + 3
        tmp2 = arg.index(' 使用 ', tmp)
        user_name = arg[tmp: tmp2]
        tmp3 = arg.index(' 获得了', tmp2)
        kusa_type = arg[tmp2 + 4: tmp3]
    elif '魔法少女' in arg:
        tmp0 = arg.index('达成') + 2
        rob_type = arg[tmp0] + '连'
        tmp = arg.index('连的玩家 ', tmp0) + 5
        tmp2 = arg.index(' 召唤了额外的', tmp)
        user_name = arg[tmp: tmp2]
        tmp3 = arg.index('魔法少女纯酱为生') + 8
        kusa_type = arg[tmp3: tmp0 - 2]

    scheduler.add_job(send_private_rob, 'date', run_date=datetime.now() + timedelta(seconds=3),
                      args=[bot, f"[CQ:face,id=144]一个{user_name}的{kusa_type}{rob_type}喜报产生了[CQ:face,id=144]"])
    # 清理围殴信息
    for data in rob_list:
        if data['endTime'] - timedelta(minutes=2) < datetime.now():
            rob_list.remove(data)
    await matcher.finish()


@rob_test.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, bot: Bot):
    await refresh_friend_list()
    msg = "免费礼炮列表："
    random.shuffle(qqList)
    for uid in qqList:
        msg += f"{uid}, "
    msg += '\n好友列表：'
    for uid in friend_list:
        if uid in qqList:
            msg += f"{uid}, "
    msg += ("\n（可以找本账号提供免费礼炮服务^_^） "
            "\n发送/免费礼炮 来获取免费礼炮"
            "\n加好友参与小礼炮私服")
    await send_msg(bot, group_id=event.group_id, message=msg)
    await matcher.finish()


@rob_free.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent):
    if event.user_id in qqList:
        qqList.remove(event.user_id)
        await send_msg2(event, '已将您从免费礼炮名单移除')
    else:
        if event.user_id != chu_id:
            qqList.append(event.user_id)
            await send_msg2(event, '已将您添加进免费礼炮名单')
        else:
            await send_msg2(event, '除除不需要使用该功能哦^ ^')
    with open(file_free_rob, mode="w", encoding='utf-8') as f2:
        f2.write(json.dumps(data_free))
    await matcher.finish()


@rob_reset_name.handle()
async def handle(matcher: Matcher, bot: Bot):
    await rename_to_itself(bot)
    await matcher.finish()


@scheduler.scheduled_job("cron", second=0)
async def rob_announce():
    for data in rob_list:
        if data['cooldown'] > 0:
            data['cooldown'] -= 1
        elif data['times'] > 0:
            percent = 100 - (data['endTime'].minute - datetime.now().minute + 60) % 60 * 5
            percent /= 100
            if random.random() < percent:
                await send_msg(bot_main, group_id=ceg_group_id, message=data['endTime'].strftime("%H:%M"))
                data['times'] -= 1
                data['cooldown'] = 10
        if data['warning'] and data['endTime'] - timedelta(minutes=3) < datetime.now():
            data['warning'] = False
            bot2 = get_bot(str(bot_main))
            for uid in qqList:
                if uid in friend_list:
                    await bot2.send_private_msg(user_id=uid, message="在途喜报将在3分钟内到来")
            if data['uid'] > 0:
                await rename_to_other(get_bot(str(data['uid'])))

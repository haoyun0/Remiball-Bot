import os
import random

from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    MessageEvent,
    Bot
)
from .myrule import isInBotList, GROUP

black_cat = on_command('黑猫', rule=isInBotList([3584213919]) & GROUP())
ball = on_command('球', rule=isInBotList([3584213919]) & GROUP())


def get_random_file(path):
    myList = []
    for root, dirs, files in os.walk(path):
        for name in files:
            myList.append(os.path.join(root, name))
    return random.choice(myList)


@black_cat.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, bot: Bot):
    file = get_random_file(r"D:\Data\gallery\黑猫")
    await bot.send_group_msg(group_id=event.group_id, message=f"[CQ:image,file=file:///{file}]")
    await matcher.finish()


@ball.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, bot: Bot):
    file = get_random_file(r"D:\Data\gallery\球")
    await bot.send_group_msg(group_id=event.group_id, message=f"[CQ:image,file=file:///{file}]")
    await matcher.finish()

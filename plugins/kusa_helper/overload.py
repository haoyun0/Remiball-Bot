from nonebot import on_command, get_driver
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    Message,
    GroupMessageEvent
)
from ..params.message_api import send_msg2
from ..params.rule import isInBotList, Message_select_group
from .config import Config

plugin_config = Config.parse_obj(get_driver().config)

overload_count = on_command('过载计算', rule=isInBotList([plugin_config.bot_main]) & Message_select_group(plugin_config.group_id_kusa))


async def differ(num: int):
    li = []
    while num > 9:
        x = num % 10
        if x not in li:
            li.append(x)
        num = num // 10
    if num not in li:
        li.append(num)
    return len(li)


@overload_count.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    args: str = arg.extract_plain_text()
    argList = args.strip().split()
    arg1 = int(argList[0])
    arg2 = int(argList[1])
    if arg2 - arg1 > 100000000:
        await send_msg2(event, "数据太大")
        await matcher.finish()
    if arg1 > arg2:
        await send_msg2(event, "小的数在前，大的数在后")
        await matcher.finish()
    p = {}
    for x in range(10):
        p[x] = 0
    for i in range(arg1, arg2 + 1):
        c = await differ(i)
        p[c] += 1
    outputStr = "过载各时段概率:"
    for x in range(10):
        if p[x] > 0:
            pc = round(100 * p[x] / (arg2 - arg1 + 1), 2)
            if pc < 0.001:
                outputStr += f"\n{x * 3}h: 几乎不可能"
            else:
                outputStr += f"\n{x * 3}h: {pc}%"
    await send_msg2(event, outputStr)
    await matcher.finish()

import asyncio

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

lianhao_count = on_command('连号计算', rule=isInBotList([plugin_config.bot_main]) & Message_select_group(plugin_config.group_id_kusa))
lock_lianhao = asyncio.Lock()


async def count_one(num: int):
    ans = []
    last = num % 10
    num = num // 10
    k = 1
    while num > 0:
        x = num % 10
        num = num // 10
        if x == last:
            k += 1
        else:
            if k >= 3:
                ans.append((k, last))
            last = x
            k = 1
        # print(num, x, last, k)
    if k >= 3:
        ans.append((k, last))
    return ans


async def count_more(arg1: int, arg2: int):
    t = {}
    for i in range(3, 10):
        t[i] = 0
    tot = 0
    l_cnt = 0
    for i in range(arg1, arg2 + 1):
        ans = await count_one(i)
        cnt = 0
        for a in ans:
            cnt += 3 ** (a[0] - 2) * ((a[1] + 1) // 3 + 1)
            t[a[0]] += 1
        if cnt > 0:
            tot += cnt
            l_cnt += 1
    d = arg2 + 1 - arg1
    outputStr = (f"{arg1}~{arg2}共{d}种可能\n"
                 f"其中共有{l_cnt}次生草触发连号\n"
                 f"连号概率为{round(100 * l_cnt / d, 3)}%\n"
                 f"每次草精期望为{round(tot / d, 3)}")
    for i in range(3, 10):
        if t[i] > 0:
            outputStr += f'\n{i}连次数为{t[i]}'
    return outputStr


@lianhao_count.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    help_str = ("两种格式\n"
                "/连号计算 num1 num2\n"
                "计算产量为num1~num2时的连号期望\n"
                "/连号计算 信息员等级(4~8) 草地数量(1~400) 生草数量等级(0~4) 是否启用沼气(y/n) 草种相关影响(1~20)\n"
                "默认启用金坷垃和使用双生法术")
    args: str = arg.extract_plain_text()
    argList = args.strip().split()
    if len(argList) == 2:
        async with lock_lianhao:
            arg1 = int(argList[0])
            arg2 = int(argList[1])
            if arg1 < 0:
                await send_msg2(event, "第一个数不能小于0")
                await matcher.finish()
            if arg2 - arg1 > 1000000:
                await send_msg2(event, "数据太大")
                await matcher.finish()
            if arg1 > arg2:
                await send_msg2(event, "小的数在前，大的数在后")
                await matcher.finish()
            outputStr = await count_more(arg1, arg2)
    elif len(argList) == 5:
        async with lock_lianhao:
            try:
                vipLevel = int(argList[0])
                if not 4 <= vipLevel <= 8:
                    raise ValueError
                grassNum = int(argList[1])
                if not 1 <= grassNum <= 400:
                    raise ValueError
                kusaNum = int(argList[2])
                if not 0 <= kusaNum <= 4:
                    raise ValueError
                kusaTechList = [1, 2.5, 4, 6, 8.4]
                other = int(argList[4])
                if not 1 <= other <= 20:
                    raise ValueError
                zz = argList[3]
                if zz not in ['y', 'n']:
                    raise ValueError
                kusa_min = 0 + 2 ** (vipLevel - 2)
                kusa_max = 10 + 2 ** (vipLevel - 2)
                kusa_min *= grassNum * other * kusaTechList[kusaNum] * 4
                kusa_max *= grassNum * other * kusaTechList[kusaNum] * 4
                if zz == 'y':
                    kusa_min *= 1.2
                    kusa_max *= 2
                kusa_min = int(kusa_min)
                kusa_max = int(kusa_max)
                outputStr = await count_more(kusa_min, kusa_max)
            except:
                outputStr = help_str
    else:
        outputStr = help_str
    await send_msg2(event, outputStr)
    await matcher.finish()

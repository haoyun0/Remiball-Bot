import asyncio
import json
import random
import re

from nonebot import on_command, on_regex, get_bots, require, get_driver
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText, CommandArg
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageEvent,
    GroupMessageEvent,
    Bot
)
from ..params.message_api import send_msg, send_msg2
from ..params.rule import PRIVATE, Message_select_group, isInBotList
from ..params.permission import SUPERUSER, isInUserList
from nonebot_plugin_apscheduler import scheduler
from .config import Config

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

bot_main = plugin_config.bot_kusa
chu_id = plugin_config.bot_chu
stone_id = plugin_config.stone_id
ceg_group_id = plugin_config.group_id_kusa
test_group_id = plugin_config.group_id_test
test2_group_id = plugin_config.group_id_test2

gather = on_command('集资', permission=SUPERUSER)
gather_account = 0
gather_items = ['自动化核心', '十连券', '高级十连券', '特级十连券']
echo = on_command('echo', rule=Message_select_group(test2_group_id),
                  permission=isInUserList([stone_id]) | SUPERUSER)
get_rank_list = on_regex('^草精新星排行榜|^总草精排行榜',
                         rule=Message_select_group(ceg_group_id) & isInBotList([bot_main]),
                         permission=isInUserList([chu_id]))
name_list = on_command('改名列表', aliases={'假面列表', '面具列表'},
                       rule=isInBotList([bot_main]), permission=SUPERUSER)

file_rank_list = 'C:/data/rank_list.txt'
is_rename_to_other = {str(plugin_config.bot_G0): False,
                      str(plugin_config.bot_G1): False,
                      str(plugin_config.bot_G2): False,
                      str(plugin_config.bot_G3): False}
name_origin = {str(plugin_config.bot_G1): '看不见的手',
               str(plugin_config.bot_G2): '提线木偶',
               str(plugin_config.bot_G0): '仿生泪滴',
               str(plugin_config.bot_G3): '抄底狂魔'}
with open(file_rank_list, mode="r", encoding='utf-8') as file:
    data_free = json.loads(file.read())
    rank_list = data_free['rank_list']
    my_rank = data_free['my_rank']

lock_rename = asyncio.Lock()
lock_send = asyncio.Lock()


@gather.handle()
async def handle(matcher: Matcher, event: MessageEvent, bot: Bot):
    global gather_account
    _ = on_regex(r'当前拥有草: \d+\n', rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([int(bot.self_id)]),
                 temp=True, handlers=[storage_handle])
    gather_account = event.user_id
    await send_msg(bot, user_id=chu_id, message='!仓库')
    await matcher.finish()


async def storage_handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    global gather_account
    tmp = arg.index('当前拥有草: ')
    kusa = int(arg[tmp + 7: arg.index('\n', tmp)])
    if kusa > 1000000:
        async with lock_send:
            await send_msg(bot, user_id=chu_id, message=f"!草转让 qq={gather_account} kusa={kusa - 1000000}")
    items = arg[arg.index('当前道具：\n') + 6:]
    lmax = len(items)
    for item in gather_items:
        if item in items:
            idx = items.index(item)
            i = idx + len(item) + 3
            num = 0
            while i < lmax and items[i].isnumeric():
                num = num * 10 + int(items[i])
                i += 1
            async with lock_send:
                await send_msg(bot, user_id=chu_id, message=f"!转让 qq={gather_account} {item} {num}")
    await matcher.finish()


@echo.handle()
async def handle(matcher: Matcher, event: GroupMessageEvent, arg: Message = CommandArg()):
    text = arg.extract_plain_text().strip()
    await send_msg2(event, text)
    await matcher.finish()


@get_rank_list.handle()
async def handle(matcher: Matcher, arg: str = EventPlainText()):
    if len(rank_list) > 10:
        await matcher.finish()
    s = arg
    for i in range(1, 26):
        pattern = f'{i}. '
        if pattern not in s:
            break
        idx = s.index(pattern)
        name = s[idx + len(pattern): s.index(':')]
        name = re.sub('[​‫‬‭‮]', '', name)
        s = s[s.index(':') + 2:]
        if 3 < len(name) <= 12:
            if name not in rank_list:
                rank_list.append(name)
    with open(file_rank_list, mode="w", encoding='utf-8') as f2:
        f2.write(json.dumps(data_free))
    await matcher.finish()


async def rename_to_other(bot: Bot):
    global lock_rename
    async with lock_rename:
        if len(rank_list) > 0:
            new_name = random.choice(rank_list)
            rank_list.remove(new_name)
        else:
            new_name = '假面骑士'
        ln = len(new_name)
        a1 = random.randint(0, ln - 2)
        new_name = new_name[0: a1] + '\u202e' + new_name[a1:]
        a2 = random.randint(a1 + 2, ln)
        new_name = new_name[0: a2] + '\u202d' + new_name[a2:]
        if await send_msg(bot, user_id=chu_id, message='!改名 ' + new_name) is not None:
            is_rename_to_other[bot.self_id] = True
    return new_name


async def rename_to_itself(bot: Bot):
    if is_rename_to_other[bot.self_id]:
        if await send_msg(bot, user_id=chu_id, message='!改名 ' + name_origin[bot.self_id]) is not None:
            is_rename_to_other[bot.self_id] = False


@scheduler.scheduled_job("cron", hour=3, minute=59, second=30)
async def handle():
    bots = get_bots()
    for bid in bots:
        bot = bots[bid]
        await rename_to_other(bot)


@scheduler.scheduled_job("cron", hour=4, minute=0, second=30)
async def handle():
    bots = get_bots()
    for bid in bots:
        bot = bots[bid]
        await rename_to_itself(bot)


@name_list.handle()
async def handle(matcher: Matcher, event: MessageEvent):
    outputStr = f"目前总共能改名为{len(rank_list)}个名字: "
    for name in rank_list:
        outputStr += '\n' + name
    await send_msg2(event, outputStr)
    await matcher.finish()


async def update_rank_once(bot: Bot, kusa: int, kusa_adv: int):
    flag = False
    uid = bot.self_id
    if kusa > my_rank[uid]['kusa_once']:
        flag = True
        my_rank[uid]['kusa_once'] = kusa
    if kusa_adv > my_rank[uid]['kusa_adv_once']:
        flag = True
        my_rank[uid]['kusa_adv_once'] = kusa_adv
    if flag:
        await send_msg(bot, group_id=test_group_id,
                       message=f"单次记录已更新为{my_rank[uid]['kusa_once']}/{my_rank[uid]['kusa_adv_once']}")
        with open(file_rank_list, mode="w", encoding='utf-8') as f2:
            f2.write(json.dumps(data_free))


async def update_rank_day(bot: Bot, kusa: int, kusa_adv: int):
    flag = False
    uid = bot.self_id
    if 'kusa_day' not in my_rank[uid]:
        my_rank[uid]['kusa_day'] = kusa
        my_rank[uid]['kusa_adv_day'] = kusa_adv
    if kusa > my_rank[uid]['kusa_day']:
        flag = True
        my_rank[uid]['kusa_day'] = kusa
    if kusa_adv > my_rank[uid]['kusa_adv_day']:
        flag = True
        my_rank[uid]['kusa_adv_day'] = kusa_adv
    if flag:
        await send_msg(bot, group_id=test_group_id,
                       message=f"简报记录已更新为{my_rank[uid]['kusa_day']}/{my_rank[uid]['kusa_adv_day']}")
        with open(file_rank_list, mode="w", encoding='utf-8') as f2:
            f2.write(json.dumps(data_free))

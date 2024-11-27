import re
from datetime import datetime, timedelta

from nonebot import on_command, on_regex
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot
)
from ..params.message_api import send_msg
from ..params.rule import isInUserList, isInBotList, PRIVATE
from .stastic import get_G_data

chu_id = 3056318700
GBot = 323690346
admin_list = [323690346, 847360401, 3584213919, 3345744507]
target = ['东', '南', '北', '珠海', '深圳']

invest_reset = on_command('G_reset',
                          rule=isInUserList(admin_list) & isInBotList([GBot]))


@invest_reset.handle()
async def handle(matcher: Matcher, bot: Bot):
    await send_msg(bot, user_id=chu_id, message='!G卖出 all')
    _ = on_regex(r'当前拥有草: \d+\n', rule=PRIVATE() & isInUserList([chu_id]) & isInBotList([GBot]),
                 temp=True, handlers=[storage_handle], expire_time=datetime.now() + timedelta(seconds=5))
    await send_msg(bot, user_id=chu_id, message='!仓库')
    await matcher.finish()


async def storage_handle(matcher: Matcher, bot: Bot, arg: str = EventPlainText()):
    G_data = await get_G_data()
    kusa = int(re.search(r'当前拥有草: (\d+)', arg).group(1))
    for i in range(5):
        invest = int(kusa / 5 / G_data[i])
        await send_msg(bot, user_id=chu_id, message=f'!G买入 {target[i][0]} {invest}')
    await matcher.finish()


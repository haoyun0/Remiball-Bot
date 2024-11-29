import re
from datetime import datetime, timedelta

from nonebot import on_command, on_regex, get_driver
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot
)
from ..params.message_api import send_msg
from ..params.rule import isInBotList, PRIVATE
from ..params.permission import isInUserList, SUPERUSER
from .stastic import get_G_data
from .config import Config

plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
GBot = plugin_config.bot_g1
target = ['东', '南', '北', '珠海', '深圳']

invest_reset = on_command('G_reset', rule=isInBotList([GBot]), permission=SUPERUSER)


@invest_reset.handle()
async def handle(matcher: Matcher, bot: Bot):
    await send_msg(bot, user_id=chu_id, message='!G卖出 all')
    _ = on_regex(r'当前拥有草: \d+\n',
                 rule=PRIVATE() & isInBotList([GBot]), permission=isInUserList([chu_id]), block=True,
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


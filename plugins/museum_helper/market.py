import base64
import json
import re
from datetime import datetime, timedelta

from nonebot import require, get_driver, on_regex, logger
from nonebot.matcher import Matcher
from nonebot.params import EventPlainText
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent
)
from ..params.message_api import send_msg, send_msg2
from ..params.rule import PRIVATE, isInBotList, isInGroupList
from .config import Config

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

base_server = 32
base_date = datetime(year=2024, month=3, day=11)
server_fix = [-149, -149, -148, -147, -145, -140, -133, -126, -118, -112, -109, -105, -101, -98, -91, -84, -80, -75, -69, -66, -59, -52, -49, -42, -38, -35, -28, -21, -14, -11, -6]

market_price = on_regex(r'^\d+[区服]市场', block=False, priority=2,
                        rule=isInGroupList(plugin_config.museum_groups) & isInBotList([plugin_config.museum_bot]))
market_data = ['小鹿饼,预计利润:5000000', '小鹿饼,预计利润:6666660', '银扳手,预计利润:4496772', '骨头,预计利润:5882352', '银扳手,预计利润:1018325', '银扳手,预计利润:7459644', '鹿粮,预计利润:9760100', '银扳手,预计利润:4477608', '小鹿饼,预计利润:3921568', '鹿粮,预计利润:2085424', '小鹿饼,预计利润:9374994', '骨头,预计利润:10465110', '银扳手,预计利润:5545590', '小鹿饼,预计利润:3846152', '骨头,预计利润:4123708', '小鹿饼,预计利润:909090', '#N/A', '银扳手,预计利润:5510187', '小鹿饼,预计利润:10526310', '骨头,预计利润:6382974', '骨头,预计利润:5000000', '小鹿饼,预计利润:11340197', '银扳手,预计利润:1075265', '猫粮,预计利润:4102560', '小鹿饼,预计利润:13592222', '骨头,预计利润:5102040', '银扳手,预计利润:9090889', '骨头,预计利润:8490564', '骨头,预计利润:1739130', '小鹿饼,预计利润:2150536', '犬粮,预计利润:4304426', '鹿粮,预计利润:4847474', '骨头,预计利润:10989010', '猫粮,预计利润:3591000', '犬粮,预计利润:5992650', '小鹿饼,预计利润:1904760', '骨头,预计利润:3030303', '鹿粮,预计利润:496770', '银扳手,预计利润:6837600', '骨头,预计利润:5000000', '骨头,预计利润:4761900', '小鹿饼,预计利润:5263155', '#N/A', '小鹿饼,预计利润:11111111', '猫粮,预计利润:959595', '银扳手,预计利润:10000000', '猫粮,预计利润:250000', '小鹿饼,预计利润:7843136', '骨头,预计利润:1000000', '猫粮,预计利润:7500000', '小鹿饼,预计利润:2040816', '骨头,预计利润:5000000', '骨头,预计利润:4761900', '银扳手,预计利润:6862730', '鹿粮,预计利润:8640630', '猫粮,预计利润:8040160', '小鹿饼,预计利润:12499992', '骨头,预计利润:3260868', '骨头,预计利润:5263155', '骨头,预计利润:10000000', '鹿粮,预计利润:648375', '小鹿饼,预计利润:11111111', '犬粮,预计利润:15097061', '鹿粮,预计利润:4400000', '银扳手,预计利润:10220400', '猫粮,预计利润:959595', '鹿粮,预计利润:9345325', '小鹿饼,预计利润:8888888', '猫粮,预计利润:12205116', '骨头,预计利润:5555555', '骨头,预计利润:1052631', '银扳手,预计利润:15062760', '犬粮,预计利润:8855678', '骨头,预计利润:10000000', '银扳手,预计利润:3846140', '猫粮,预计利润:210412', '小鹿饼,预计利润:8791208', '猫粮,预计利润:5250000', '犬粮,预计利润:1079673', '小鹿饼,预计利润:12222221', '骨头,预计利润:8695648', '银扳手,预计利润:10000000', '小鹿饼,预计利润:990099', '猫粮,预计利润:4168668', '银扳手,预计利润:925925', '犬粮,预计利润:5052525', '小鹿饼,预计利润:1086956', '骨头,预计利润:20879119', '小鹿饼,预计利润:1098901', '小鹿饼,预计利润:19565208', '银扳手,预计利润:1041665', '鹿粮,预计利润:4738125', '骨头,预计利润:11111110']


@market_price.handle()
async def handle(matcher: Matcher, event: MessageEvent, msg: str = EventPlainText()):
    r = re.match(r"(\d+)[区服]市场", msg)
    server = int(r.group(1))

    today = datetime.now()

    if server >= base_server:
        server_date = base_date + timedelta(days=(server - base_server) * 7)
        if today < server_date:
            await send_msg2(event, f'{server}服还没开呢')
            await matcher.finish()
    else:
        server_date = base_date + timedelta(days=server_fix[server - base_server])
    td = today - server_date

    if td.days <= 279:
        recommend_raw = market_data[td.days % 93]
    else:
        recommend_raw = market_data[(td.days - 1) % 93]
    if recommend_raw != '#N/A':
        r = re.search(r'(.*?),预计利润:(\d+)', recommend_raw)
        recommend = f'推荐购买{r.group(1)}, 预计利润:{round(int(r.group(2)) / 1000000, 2)}%'
    else:
        recommend = '今日全跌，不推荐购买'
    outputStr = f'[CQ:reply,id={event.message_id}]{server}服开服第{td.days + 1}天\n{recommend}'
    await send_msg2(event, outputStr)

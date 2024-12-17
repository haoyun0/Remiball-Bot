import base64
import json
import re
from datetime import datetime, timedelta

from nonebot import require, get_driver, on_message, logger, on_command
from nonebot.matcher import Matcher
from nonebot.params import EventMessage, CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent
)
from ..params.message_api import send_msg, send_msg2
from ..params.rule import PRIVATE, isInBotList, isInGroupList
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

# [CQ:json,data={"app":"com.tencent.mannounce"&#44;"bizsrc":""&#44;"config":{"ctime":1733113592&#44;"forward":0&#44;"token":"393a7c0807fe2a1d021a2a8fad721c6b"}&#44;"extra":{"app_type":1&#44;"appid":1101236949&#44;"uin":847360401}&#44;"meta":{"mannounce":{"cr":0&#44;"encode":1&#44;"fid":"ea049c1000000000f8364d6791ce0000"&#44;"gc":"278660330"&#44;"sign":"e3e0e54786e2373531febad1e86c2baa"&#44;"text":"MTLmnIgy5pel56S85YyF56CB77ya5oyH55Sy57q557qi6Zm25aO2Ci0tLS0tLS0tLS0tLS0tLS0tLQrnlJ/mlYjml7bpl7TvvJrlvZPlpKkwOTowMArlpLHmlYjml7bpl7TvvJrmrKHml6UxMjowMArpooblj5bnpLzljIXnoIHmlrnlvI/vvJrkuLvnlYzpnaLigJTigJTngrnlh7vlt6bkuIrop5Lppobplb/lpLTlg4/igJTigJTorr7nva7igJTigJTkuIvmlrnovpPlhaXnpLzljIXnoIHlkI7ngrnlh7vpooblj5Yu"&#44;"title":"576k5YWs5ZGK"&#44;"tw":1&#44;"uin":"847360401"}}&#44;"prompt":"&#91;群公告&#93;12月2日礼包码：指甲纹红陶壶------------------生效时间：当天09:00失效时间：次日12:00领取礼包码方式：主界面——点击左上角馆长头像——设置——下方输入礼包码后点击领…"&#44;"ver":"1.0.0.43"&#44;"view":"main"}]
museum_msg = on_message(rule=isInGroupList(plugin_config.museum_groups) & isInBotList([plugin_config.museum_bot]),
                        block=False, priority=1)


try:
    with open(r'C:/Data/museum_giftCode.txt', 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
except:
    data = {}


async def savefile():
    with open(r'C:/Data/museum_giftCode.txt', 'w', encoding='utf-8') as s:
        s.write(json.dumps(data))


@museum_msg.handle()
async def handle(matcher: Matcher, event: MessageEvent, bot: Bot, msg: Message = EventMessage()):
    r = re.search(r"\[CQ:json,data=(.*)]", str(msg))
    if r is not None:
        json_data = json.loads(r.group(1).replace('&#44;', ', '))
        # 群公告
        if json_data['app'] == 'com.tencent.mannounce':
            text_raw = json_data['meta']['mannounce']['text']
            text = base64.b64decode(bytes(text_raw, 'utf-8')).decode('utf-8')
            r2 = re.findall(r'(\d+)月(\d+)日礼包码：(.*)\n', text)
            if len(r2) > 0:
                t = datetime.now()
                for g in r2:
                    while int(g[0]) != t.month or int(g[1]) != t.day:
                        t = t + timedelta(days=1)
                    date = t.strftime("%Y-%m-%d")
                    data[date] = g[2].strip()
                await savefile()
                date = datetime.now().strftime("%Y-%m-%d")
                await send_msg2(event, data[date])
    else:
        if len(str(msg)) < 20:
            r2 = re.search(r"昨[天|日].*?[码吗麻嘛妈马玛]是.*?(啥|什么|\?|？).*?", str(msg))
            if r2 is not None:
                t = datetime.now() - timedelta(days=1)
                date = t.strftime("%Y-%m-%d")
                if date in data:
                    outputMsg = f"[CQ:reply,id={event.message_id}]" + data[date]
                    outputMsg += "\n但是可能已经失效了" if t.hour >= 12 else ""
                    await send_msg2(event, outputMsg)
            r3 = re.search(r"今[天|日].*?[码吗麻嘛妈马玛]是.*?(啥|什么|\?|？).*?", str(msg))
            if r3 is not None:
                t = datetime.now()
                date = t.strftime("%Y-%m-%d")
                if date in data:
                    outputMsg = f"[CQ:reply,id={event.message_id}]" + data[date]
                    outputMsg += "\n但是要九点之后才能用" if t.hour < 9 else ""
                    await send_msg2(event, outputMsg)
                else:
                    await send_msg2(event, f"[CQ:reply,id={event.message_id}]还没发")
    await matcher.finish()


@scheduler.scheduled_job('cron', hour=9)
async def handle():
    date = datetime.now().strftime("%Y-%m-%d")
    for gid in plugin_config.museum_groups:
        if date in data:
            await send_msg(plugin_config.museum_bot, group_id=gid, message=data[date])

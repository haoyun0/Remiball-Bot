from datetime import datetime, timedelta

from matplotlib import pyplot as plt
from nonebot import on_command, get_driver
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
)
from ..params.message_api import send_msg2
from ..params.rule import isInBotList, Message_select_group
from .bank import freeze_depend
from .config import Config

plugin_config = Config.parse_obj(get_driver().config)

ceg_group_id = plugin_config.group_id_kusa
bot_bank = plugin_config.bot_main
file = 'C:/Data/Cache/G_all.png'

G_pic = on_command('G线图', rule=Message_select_group(ceg_group_id) & isInBotList([bot_bank]))


async def draw_G_pic(G_data: dict, reverse: bool = False):
    gValuesColMap = getGValuesColMap(G_data)
    await createGpicAll(gValuesColMap, file, reverse)


async def createGpicAll(gValuesColMap, gPicPath, reverse):
    plt.plot(list(map(lambda x: x / 9.8, gValuesColMap['eastValue'])), label='East')
    plt.plot(list(map(lambda x: x / 9.8, gValuesColMap['southValue'])), label='South')
    plt.plot(list(map(lambda x: x / 6.67, gValuesColMap['northValue'])), label='North')
    plt.plot(list(map(lambda x: x / 32.0, gValuesColMap['zhuhaiValue'])), label='Zhuhai')
    plt.plot(list(map(lambda x: x / 120.0, gValuesColMap['shenzhenValue'])), label='Shenzhen')
    plt.xticks([])
    plt.yscale('log')
    if reverse:
        plt.gca().invert_yaxis()
        plt.legend().set_loc(2)
    else:
        plt.legend()
    plt.savefig(gPicPath)
    plt.close()


def getGValuesColMap(G_data: dict):
    gValuesColMap = {'eastValue': [], 'southValue': [], 'northValue': [], 'zhuhaiValue': [], 'shenzhenValue': []}
    tmp = datetime.now()
    date = tmp.strftime("%Y-%m-%d")
    while date not in G_data:
        tmp -= timedelta(days=1)
        date = tmp.strftime("%Y-%m-%d")
    for i in range(1, 146):
        if str(i) in G_data[date]:
            gValuesColMap['eastValue'].append(G_data[date][str(i)][0])
            gValuesColMap['southValue'].append(G_data[date][str(i)][1])
            gValuesColMap['northValue'].append(G_data[date][str(i)][2])
            gValuesColMap['zhuhaiValue'].append(G_data[date][str(i)][3])
            gValuesColMap['shenzhenValue'].append(G_data[date][str(i)][4])
    return gValuesColMap


@G_pic.handle(parameterless=[Depends(freeze_depend)])
async def handle(matcher: Matcher, event: GroupMessageEvent):
    await send_msg2(event, f"[CQ:image,file=file:///{file}]")
    await matcher.finish()

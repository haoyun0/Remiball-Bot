import asyncio
from nonebot import get_driver
from nonebot.params import Matcher
from nonebot.adapters.onebot.v11 import MessageEvent
from .config import Config

plugin_config = Config.parse_obj(get_driver().config)

lock_receive = asyncio.Lock()
receive_msg_id = []


def isSubAccount(user_id: str) -> bool:
    """
    判断一个qq号是否为小号
    :param user_id: 用户qq号
    :return: bool
    """
    return user_id in plugin_config.sub_accounts


async def handleOnlyOnce(matcher: Matcher, event: MessageEvent):
    """
    判断一条消息是否已经被响应过，适用于多个处理器为同一优先度的情况
    """
    async with lock_receive:
        if event.message_id in receive_msg_id:
            await matcher.finish()
        receive_msg_id.append(event.message_id)
        return matcher

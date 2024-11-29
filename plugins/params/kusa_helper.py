import asyncio
from nonebot import get_driver

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


async def isReceiveValid(msg_id: int) -> bool:
    """
    判断一条消息是否已经被响应过，适用于多个处理器为同一优先度的情况
    :param msg_id: 消息id
    :return: bool
    """
    async with lock_receive:
        if msg_id in receive_msg_id:
            return False
        receive_msg_id.append(msg_id)
        return True

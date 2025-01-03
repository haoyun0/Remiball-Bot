import asyncio
from typing import Union
from nonebot import get_bot, logger, get_driver
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent
)

from .config import Config

plugin_config = Config.parse_obj(get_driver().config)
lock_chu: dict[str, asyncio.Lock] = {}
bot_id_chu = plugin_config.bot_chu


async def send_msg(bot: Union[Bot, int, str], message: str, group_id: int = 0, user_id: int = 0):
    """
    通用发消息api
    :param bot: 可为Bot, int, str
    :param message: 消息内容
    :param group_id: 如果发群消息，则填群号
    :param user_id: 如果发私聊消息，则填用户qq号
    :return: message_id
    """
    if isinstance(bot, (int, str)):
        try:
            bot: Bot = get_bot(str(bot))
        except:
            return None
    if group_id > 0:
        try:
            return await bot.send_group_msg(group_id=group_id, message=message)
        except:
            logger.error(f'发送到{group_id}的群消息发送失败，消息内容为:\n{message}')
            return None
    else:
        if user_id != bot_id_chu:
            try:
                return await bot.send_private_msg(user_id=user_id, message=message)
            except:
                logger.error(f'发送到{user_id}的私聊消息发送失败，消息内容为:\n{message}')
                return None
        else:
            # 单纯是为了防止给除草器刷指令
            if bot.self_id not in lock_chu:
                lock_chu[bot.self_id] = asyncio.Lock()
            async with lock_chu[bot.self_id]:
                try:
                    tmp = await bot.send_private_msg(user_id=user_id, message=message)
                    await asyncio.sleep(1.5)
                    return tmp
                except:
                    logger.error(f'发送到{user_id}的私聊消息发送失败，消息内容为:\n{message}')
                    return None


async def send_msg2(event: MessageEvent, message: str):
    """
    通用发消息api，根据事件自动回复
    :param event: MessageEvent
    :param message: 消息内容
    :return: message_id
    """
    if event.message_type == 'group':
        event: GroupMessageEvent
        bot: Bot = get_bot(str(event.self_id))
        return await send_msg(bot, group_id=event.group_id, message=message)
    elif event.message_type == 'private':
        event: PrivateMessageEvent
        bot: Bot = get_bot(str(event.self_id))
        return await send_msg(bot, user_id=event.user_id, message=message)
    else:
        return None

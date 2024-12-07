from nonebot.internal.rule import Rule
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    MessageEvent
)


def Message_select_group(group_id: int) -> Rule:
    """
    只在特定群聊
    :param group_id: 群号
    :return: Rule
    """
    async def _enable(event: MessageEvent) -> bool:
        if event.message_type == 'group':
            if event.group_id == group_id:
                return True
        return False
    return Rule(_enable)


def PRIVATE() -> Rule:
    async def _isPrivate(event: MessageEvent) -> bool:
        return event.message_type == 'private'
    return Rule(_isPrivate)


def GROUP() -> Rule:
    async def _isPrivate(event: MessageEvent) -> bool:
        return event.message_type == 'group'
    return Rule(_isPrivate)


def isInBotList(bots: list[int]) -> Rule:
    """
    收到事件的Bot的在列表内
    :param bots: list[int]
    :return: Rule
    """
    async def _enable(event: MessageEvent) -> bool:
        if event.self_id in bots:
            return True
        return False
    return Rule(_enable)


def isInGroupList(groups: list[int]) -> Rule:
    """
    只在特定群聊
    :param groups: list[int] 群号列表
    :return: Rule
    """
    async def _enable(event: MessageEvent) -> bool:
        if event.message_type == 'group':
            if event.group_id in groups:
                return True
        return False
    return Rule(_enable)

from nonebot.internal.rule import Rule
from nonebot.adapters.onebot.v11 import (
    MessageEvent
)


def Message_select_group(group_id: int) -> Rule:
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


def isInUserList(users: list) -> Rule:
    async def _enable(event: MessageEvent) -> bool:
        if event.user_id in users:
            return True
        return False
    return Rule(_enable)


def isInBotList(bots: list) -> Rule:
    async def _enable(event: MessageEvent) -> bool:
        if event.self_id in bots:
            return True
        return False
    return Rule(_enable)

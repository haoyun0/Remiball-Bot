from nonebot.internal.permission import Permission
from nonebot.permission import SUPERUSER
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import (
    MessageEvent
)


def isInUserList(users: list[int]) -> Permission:
    """
    触发指令的用户在列表内
    :param users: list[int]
    :return: Permission
    """

    async def _enable(event: MessageEvent) -> bool:
        if event.user_id in users:
            return True
        return False

    return Permission(_enable)

from nonebot.internal.rule import Rule
from nonebot.adapters.onebot.v11 import (
    MessageEvent
)


def isBot(bot: int) -> Rule:
    async def _enable(event: MessageEvent) -> bool:
        if event.self_id == bot:
            return True
        return False
    return Rule(_enable)

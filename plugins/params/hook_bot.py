from nonebot.message import run_preprocessor
from nonebot.exception import IgnoredException
from nonebot import get_driver, logger
from nonebot.adapters.onebot.v11 import Event
from nonebot.params import Matcher
from nonebot.plugin import Plugin
from .config import Config

plugin_config = Config.parse_obj(get_driver().config)


@run_preprocessor
async def do_something(event: Event, matcher: Matcher):
    if event.self_id != plugin_config.bot_main:
        plugin: Plugin = matcher.plugin
        # logger.error(f"{event.self_id}: {plugin.module_name}")
        if plugin.module_name not in plugin_config.except_plugins:
            raise IgnoredException("some reason")

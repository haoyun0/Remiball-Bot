import re
from typing import Union

from nonebot import get_driver, on_command, on_fullmatch
from nonebot.adapters.onebot.v11 import Message
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from .img_tool import img2bytes
from .manager import MenuManager
from .metadata import __plugin_meta__ as __plugin_meta__
from .config import Config
from .rule import help_rule

driver = get_driver()
plugin_config = Config.parse_obj(driver.config)


@driver.on_startup
async def _():
    if not menu_manager.data_manager.plugin_menu_data_list:
        menu_manager.load_plugin_info()


menu_manager = MenuManager()

menu = on_command("菜单", aliases={"功能", "帮助", "help"},
                  priority=plugin_config.help_priority, block=plugin_config.help_block, rule=help_rule)


@menu.handle()
async def _(matcher: Matcher, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()

    if not msg:  # 参数为空，主菜单
        img = menu_manager.generate_main_menu_image()
        await matcher.finish(MessageSegment.image(img2bytes(img)))

    match_result = re.match(r"^(?P<name>.*?)( (?P<cmd>.*?))?$", msg)
    if not match_result:
        return

    plugin_name: str = match_result["name"]
    cmd: Union[str, None] = match_result["cmd"]

    if cmd:  # 三级菜单
        temp = menu_manager.generate_func_details_image(plugin_name, cmd)

        if not isinstance(temp, str):
            await matcher.finish(MessageSegment.image(img2bytes(temp)))

        if temp == "PluginIndexOutRange":
            await matcher.finish("插件序号不存在")
        if temp == "CannotMatchPlugin":
            await matcher.finish("插件名过于模糊或不存在")
        if temp == "PluginNoFuncData":
            await matcher.finish("该插件无功能数据")
        if temp == "CommandIndexOutRange":
            await matcher.finish("命令序号不存在")
        await matcher.finish("命令过于模糊或不存在")

    else:  # 二级菜单
        temp = menu_manager.generate_plugin_menu_image(plugin_name)

        if not isinstance(temp, str):
            await matcher.finish(MessageSegment.image(img2bytes(temp)))

        if temp == "PluginIndexOutRange":
            await matcher.finish("插件序号不存在")
        await matcher.finish("插件名过于模糊或不存在")

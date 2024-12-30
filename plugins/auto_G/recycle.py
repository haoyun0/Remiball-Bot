import asyncio
import json
import math
import random
import re
from datetime import datetime, timedelta
from typing import Annotated

from nonebot import require, on_command, on_regex, get_driver
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, EventPlainText, T_State, Depends
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    Message,
    Bot
)
from ..params.message_api import send_msg, send_msg2
from ..params.kusa_helper import isSubAccount, handleOnlyOnce
from ..params.rule import Message_select_group, isInBotList, PRIVATE
from ..params.permission import SUPERUSER, isInUserList
from .config import Config
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)

chu_id = plugin_config.bot_chu
ceg_group_id = plugin_config.group_id_kusa
notice_id = plugin_config.bot_g1
bot_bank = plugin_config.bot_main




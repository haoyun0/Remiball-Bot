from pydantic import BaseModel, Extra
from typing import Optional


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    bot_chu: Optional[int] = 0  # 除草器Bot的qq号
    SUPERUSERS: Optional[list] = []
    sub_accounts: Optional[list] = []  # 小号名单

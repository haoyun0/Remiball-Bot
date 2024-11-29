from pydantic import BaseModel, Extra
from typing import Optional


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    bot_chu: Optional[int] = 0  # 除草器Bot的qq号
    bot_main: Optional[int] = 0  # 主要Bot的qq号
    group_id_kusa: Optional[int] = 0  # 测G群的群号

from pydantic import BaseModel, Extra
from typing import Optional


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    bot_chu: Optional[int] = 0  # 除草器Bot的qq号
    bot_kusa: Optional[int] = 0  # 生草功能主要Bot的qq号
    bot_main: Optional[int] = 0  # 主要Bot的qq号
    bot_G0: Optional[int] = 0  # 其他Bot的qq号
    bot_G1: Optional[int] = 0  # 其他Bot的qq号
    bot_G2: Optional[int] = 0  # 其他Bot的qq号
    bot_G3: Optional[int] = 0  # 其他Bot的qq号
    group_id_test: Optional[int] = 0  # 测G群的群号
    group_id_kusa: Optional[int] = 0  # 测G群的群号
    stone_id: Optional[int] = 0  # 小石子的qq号
    group_id_test2: Optional[int] = 0  # 测试广场的群号

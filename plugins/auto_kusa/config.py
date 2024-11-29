from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    bot_chu: int = 0  # 除草器Bot的qq号
    bot_kusa: int = 0  # 生草功能主要Bot的qq号
    bot_main: int = 0  # 主要Bot的qq号
    bot_G0: int = 0  # 其他Bot的qq号
    bot_G1: int = 0  # 其他Bot的qq号
    bot_G2: int = 0  # 其他Bot的qq号
    bot_G3: int = 0  # 其他Bot的qq号
    group_id_test: int = 0  # 测G群的群号
    group_id_kusa: int = 0  # 测G群的群号
    stone_id: int = 0  # 小石子的qq号
    group_id_test2: int = 0  # 测试广场的群号

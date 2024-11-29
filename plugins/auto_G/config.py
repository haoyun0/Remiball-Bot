from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    bot_chu: int = 0  # 除草器Bot的qq号
    bot_main: int = 0  # 主要Bot的qq号
    bot_g0: int = 0  # 其他Bot的qq号1
    bot_g1: int = 0  # 其他Bot的qq号2
    bot_g2: int = 0  # 其他Bot的qq号3
    bot_g3: int = 0  # 其他Bot的qq号4
    group_id_test: int = 0  # 测G群的群号
    group_id_kusa: int = 0  # 测G群的群号
    g_follow_accounts: set[str] = set()  # 跟G策略的qq号

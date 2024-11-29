from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    bot_chu: int = 0  # 除草器Bot的qq号
    bot_main: int = 0  # 主要Bot的qq号
    group_id_kusa: int = 0  # 测G群的群号

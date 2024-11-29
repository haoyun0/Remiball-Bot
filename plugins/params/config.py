from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    bot_chu: int = 0  # 除草器Bot的qq号
    sub_accounts: set[str] = set()  # 小号名单

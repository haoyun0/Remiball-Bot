from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    bot_chu: int = 0  # 除草器Bot的qq号
    bot_main: int = 0  # 主要Bot的qq号，其他Bot将不处理任何事件除非插件在下列排除名单中
    except_plugins: set[str] = set()  # 其他Bot也能运行的插件名单
    sub_accounts: set[str] = set()  # 小号名单

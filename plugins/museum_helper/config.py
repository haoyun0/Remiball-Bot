from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # Your Config Here
    museum_bot: int = 0
    museum_groups: list[int] = []

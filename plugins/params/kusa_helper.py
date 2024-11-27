import asyncio

sub_name_list = {
    "323690346": ["3584213919", "3345744507", "847360401"],
    "1204054189": ["3923807804"],
    "617181540": ["354039591"],
    "2834968795": ["261301604", "2197757582", "2336343527", "3527232937", "3639551646"],
    "3150152495": ["2072009684", "3056318700"],
    "1005180705 ": ["2809598783", "3665792041", "1923193853", "3874559707"],
    "1789672864": ["3434862448", "3304481613"],
    "2163252003": ["1945620694"],
    "519147878": ["2182291769"],
    "702405035": ["871900058"],
    "2579334078": ["3518925014"],
    "1045714082": ["3820442296"]
}

lock_receive = asyncio.Lock()
receive_msg_id = []


def isSubAccount(user_id: str):
    for uid in sub_name_list:
        if user_id in sub_name_list[uid]:
            return True
    return False


async def isReceiveValid(msg_id: int):
    async with lock_receive:
        if msg_id in receive_msg_id:
            return False
        receive_msg_id.append(msg_id)
        return True

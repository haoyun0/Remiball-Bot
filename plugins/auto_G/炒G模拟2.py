import asyncio
from datetime import datetime
from random import random

chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
admin_idlist = [323690346, 847360401, 3584213919, 3345744507]

num_conclude = 0
log_level = 2


init_flag = False
target = ['东', '南', '北', '珠海', '深圳']
target_init = [9.8, 9.8, 6.67, 32.0, 120.0]
target_change = [0.075, 0.1, 0.075, 0.1, 0.15]
G_sm = {}
try:
    raise ValueError
    # with open(r'C:/Data/G_data.txt', 'r', encoding='utf-8') as f:
    #     data = json.loads(f.read())
except:
    data = {
        'turn': -1,
        'invest': 200000000,
        'update_minute': datetime.now().minute,
        'update_hour': datetime.now().hour - 1
    }
    data2 = {
        'coin': 0,
        'invest_times': 0,
        'value_in': 0,
        'value_max': 0.0,
        'value_last': 0.0
    }
    for i_x in range(5):
        data[target[i_x]] = data2.copy()
        G_sm[target[i_x]] = 0


def logger(msg: str, level: int = 1):
    global log_level
    if level > log_level:
        print(msg)


async def handle_once(turn_new: int, G_new: list):
    global init_flag, G_sm
    str1 = f'周期: {turn_new}'
    str2 = ""
    for i in range(5):
        # await asyncio.sleep(1)
        t = target[i]
        t2 = t + '校区：'
        value_new = G_new[i]
        str1 += f', {t[0]}: {value_new}'
        if value_new > data[t]['value_max']:
            data[t]['value_max'] = value_new

        if not init_flag:
            G_now = G_sm[t]
            if (data[t]['value_max'] - data[t]['value_in']) / data[t]['value_in'] > target_change[i] * 2:
                invest = int(data['invest'] / 2 / value_new)
                if G_now > invest:
                    x = 1
                    while G_now / 2 > invest * (x + 1):
                        x += 1
                    data[t]['invest_times'] -= x
                    str2 += f'\n决策减仓卖出{invest * x}{t[0]}G, 买入价{data[t]["value_in"]}'
                    G_sm[t] -= invest * x
                    data[t]['value_max'] = value_new
                    data[t]['value_in'] = value_new
            elif (data[t]['value_max'] - value_new) / data[t]['value_max'] > target_change[i] * 1.5:
                if (data[t]['value_max'] - data[t]['value_in']) / data[t]['value_in'] > target_change[i] * 0.5:
                    data[t]['value_max'] = value_new
                    data[t]['value_in'] = value_new
                else:
                    if value_new < data[t]['value_last']:
                        if data[t]['invest_times'] < 2:
                            data[t]['invest_times'] += 1
                            invest = int(data['invest'] / 2 / value_new)
                            str2 += f'\n决策套牢买入{invest}{t[0]}G, 高峰{data[t]["value_max"]}'
                            G_sm[t] += invest
                            data[t]['value_max'] = value_new
                            data[t]['value_in'] = value_new
        elif init_flag:
            invest = int(data[t]['coin'] / value_new)
            # str2 += f'\n决策初始买入{invest}{t[0]}G'
            data[t]['value_max'] = value_new
            data[t]['value_in'] = value_new
            G_sm[t] = invest
        data[t]['value_last'] = value_new
    data['update_minute'] = datetime.now().minute
    data['update_hour'] = datetime.now().hour
    str1 = str1.strip()
    logger(str1, 1)
    str2 = str2.strip()
    if len(str2) > 0:
        logger(str2, 2)
    # await bot.send_private_msg(user_id=323690346, message=str1 + str2 + f'\n盈亏估值:{num_conclude}')
    if init_flag:
        init_flag = False


async def handle_turn():
    for i in range(5):
        t = target[i]
        data[t]['coin'] = data['invest']
        data[t]['invest_times'] = 0
        G_sm[t] = 0
    G1 = 9.8
    G2 = 9.8
    G3 = 6.67
    G4 = 32.0
    G5 = 120.0
    global init_flag
    init_flag = True
    for i in range(0, 145):
        await handle_once(i + 1, [G1, G2, G3, G4, G5])
        G1 *= 1 + 0.075 * (random() - 0.498)
        G1 = round(G1, 3)
        G2 *= 1 + 0.1 * (random() - 0.498)
        G2 = round(G2, 3)
        G3 *= 1 + 0.075 * (random() - 0.498)
        G3 = round(G3, 3)
        G4 *= 1 + 0.1 * (random() - 0.498)
        G4 = round(G4, 3)
        G5 *= 1 + 0.15 * (random() - 0.498)
        G5 = round(G5, 3)
    coin_in = 0
    for i in range(5):
        t = target[i]
        coin_in += round(data['invest'] * (data[t]['invest_times'] * 0.5 + 1))
    coin_final = round(G1 * G_sm['东'] + G2 * G_sm['南'] + G3 * G_sm['北'] + G4 * G_sm['珠海'] + G5 * G_sm['深圳'])
    logger(f'盈亏估值{coin_final - coin_in}', 3)
    return coin_final - coin_in


async def handle_more(turns: int):
    coin = 10 * 100000000
    for _ in range(turns):
        data['invest'] = coin // 10
        result = await handle_turn()
        coin += result
    logger(f"最终持有{round(coin / 100000000, 2)}e", 4)


log_level = 3
asyncio.run(handle_more(1000))

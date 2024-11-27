import asyncio
from datetime import datetime
from random import random
import matplotlib.pyplot as plt

chu_id = 3056318700
ceg_group_id = 738721109
test_group_id = 278660330
admin_idlist = [323690346, 847360401, 3584213919, 3345744507]

num_conclude = 0
log_level = 2

divide = 10
divide2 = 1
run_limit = 2
init_flag = False
target = ['东', '南', '北', '珠海', '深圳']
target_init = [9.8, 9.8, 6.67, 32.0, 120.0]
target_change = [0.1, 0.1, 0.08, 0.1, 0.15]
G_sm = {}
try:
    raise ValueError
    # with open(r'C:/Data/G_data.txt', 'r', encoding='utf-8') as f:
    #     data = json.loads(f.read())
except:
    data = {
        'turn': -1,
        'invest': 200000000,
        'invest_total': 0,
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
        t = target[i]
        value_new = G_new[i]
        str1 += f', {t[0]}: {value_new}'
        if value_new > data[t]['value_max']:
            data[t]['value_max'] = value_new

        if not init_flag:
            G_now = G_sm[t]
            if (data[t]['value_max'] - data[t]['value_in']) / data[t]['value_in'] > target_change[i] / 2:
                if data[t]['invest_times'] < divide and data['invest_total'] < divide * 10:
                    data[t]['invest_times'] += 1
                    data['invest_total'] += 1
                    invest = int(data['invest'] / divide / value_new)
                    str2 += f'\n决策套牢买入{invest}{t[0]}G, 高峰{data[t]["value_max"]}'
                    G_sm[t] += invest

                    data[t]['value_max'] = value_new
                    data[t]['value_in'] = value_new
            elif (data[t]['value_max'] - value_new) / data[t]['value_max'] > target_change[i] / 2:
                if value_new < data[t]['value_last']:
                    invest = int(data['invest'] / divide / value_new)
                    if G_now > invest:
                        x = 1
                        # while G_now / 2 > invest * (x + 1):
                        #     x += 1
                        data[t]['invest_times'] -= x
                        data['invest_total'] -= x
                        str2 += f'\n决策减仓卖出{invest * x}{t[0]}G, 买入价{data[t]["value_in"]}'
                        G_sm[t] -= invest * x

                        data[t]['value_max'] = value_new
                        data[t]['value_in'] = value_new


        elif init_flag:
            invest = int(data['invest'] / value_new * 1.6)
            # str2 += f'\n决策初始买入{invest}{t[0]}G'
            data[t]['value_max'] = value_new
            data[t]['value_in'] = value_new
            G_sm[t] = invest
        data[t]['value_last'] = value_new
    str1 = str1.strip()
    logger(str1, 1)
    str2 = str2.strip()
    if len(str2) > 0:
        logger(str2, 2)
    # await bot.send_private_msg(user_id=323690346, message=str1 + str2 + f'\n盈亏估值:{num_conclude}')
    if init_flag:
        data['invest_total'] = divide * 8
        init_flag = False


async def handle_turn():
    G_handle = []
    for i in range(5):
        t = target[i]
        data[t]['coin'] = data['invest'] * 1
        data[t]['invest_times'] = 0
        G_sm[t] = 0
        G_handle.append(target_init[i])
    global init_flag
    init_flag = True
    await handle_once(1, G_handle)
    for k in range(1, 144 // divide2 + 1):
        for i in range(5):
            G_handle[i] *= 1 + target_change[i] * (random() - 0.498)
            G_handle[i] = round(G_handle[i], 3)
        await handle_once(k + 1, G_handle)
        # coin_now = 0
        # coin_in = 0
        # for i in range(5):
        #     t = target[i]
        #     coin_in += round(data['invest'] * (data[t]['invest_times'] * 0.5 + 1))
        #     coin_now += round(G_handle[i] * G_sm[target[i]])
        # if (coin_now - coin_in) / coin_in > 0.3:
        #     break

    coin_in = round(data['invest'] * data['invest_total'] / divide)
    coin_final = 0
    for i in range(5):
        # t = target[i]
        # coin_in += round(data['invest'] * (data[t]['invest_times'] * 0.5 + 1))
        coin_final += round(G_handle[i] * G_sm[target[i]])
    logger(f'盈亏估值{coin_final - coin_in}', 3)
    return coin_final - coin_in


async def handle_more(turns: int):
    # turns *= divide2
    coin = 10 * 100000000 # * 100000000
    total_ratio = 0
    ratio_min = 0
    ratio_max = 0
    win = 0
    lose = 0
    ratios = []
    for _ in range(turns):
        tmp_coin = 11 * 100000000
        for __ in range(divide2):
            # data['invest'] = 100000000
            data['invest'] = tmp_coin // 11
            result = await handle_turn()
            tmp_coin += result
        # ratio = result / coin
        result = tmp_coin - 1100000000
        if result > 0:
            win += 1
        else:
            lose += 1
        ratio = result / 1100000000
        ratios.append(ratio)
        if ratio < ratio_min:
            ratio_min = ratio
        if ratio > ratio_max:
            ratio_max = ratio
        total_ratio += ratio
        coin *= 1 + ratio
    logger(f"最终持有{round(coin / 100000000, 2)}e", 4)
    logger(f"每周期收益率{round(total_ratio / turns * 100, 3)}%", 4)
    logger(f"最小/大收益率{round(ratio_min * 100, 3)}%, {round(ratio_max * 100, 3)}%", 4)
    ff = 30000 / 10
    logger(f"收益正:{win}, 收益负:{lose}, 比率{round(win / ff, 2)}:{round(lose / ff, 2)}", 4)
    plt.hist(ratios, bins=100, edgecolor='black', linewidth=1.2)

    # 设置标题和轴标签
    plt.title('Histogram of Data')
    plt.xlabel('Value')
    plt.ylabel('Frequency')

    plt.show()


log_level = 3
asyncio.run(handle_more(30000))

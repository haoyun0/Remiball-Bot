import random
systemRandom = random.SystemRandom()


turns = 10000
total = 0
t_min = 0
t_max = 0
st = 5 * 100000000
cnt_n = 0
cnt_p = 0
G_type = 0.15
for _ in range(turns):
    e = 100000000
    G_in = e // 120
    coin_in = G_in * 120
    coin_now = 0
    coin_in_times = 0
    base_max = 120
    base_in = 120
    buy_in_cnt = 0
    G = 120
    G_list = [120]
    divide = 2
    for i in range(1, 145):
        G *= 1 + G_type * (random.random() - 0.498)
        G_list.append(G)
        if G > base_max:
            base_max = G
        if G_in > 0:
            if (base_max - base_in) / base_in > G_type * 2:
                tmp = e / divide // G
                if G_in > tmp:
                    x = 1
                    while G_in / 2 > tmp * (x + 1):
                        x += 1
                    coin_in -= tmp * G * x
                    coin_in_times -= x
                    base_max = G
                    base_in = G
                    G_in -= tmp * x
            elif (base_max - G) / base_max > G_type * 1.5:
                if (base_max - base_in) / base_in > G_type * 0.5:
                    base_max = G
                    base_in = G
                else:
                    if G < G_list[i - 1]:
                        if coin_in_times < divide:
                            coin_in_times += 1
                            tmp = e / divide // G
                            coin_in += tmp * G
                            G_in += tmp
                            base_in = G
                            base_max = G
                        else:
                            base_in = G
                            base_max = G
                            pass
    coin_now += G_in * G
    delta = coin_now - coin_in
    total += delta
    if delta > 0:
        cnt_p += 1
    else:
        cnt_n += 1
    t_max = max(t_max, delta)
    t_min = min(t_min, delta)
    # print(f'本周期净利润{round((coin_now - coin_in)/1000000, 2)}m, 最大持仓{round(coin_in/100000000, 2)}e, 利润百分比{round((coin_now - coin_in)/coin_in*100, 2)}%')
    # print(delta, t_min, t_max)
    ratio = st / 6 / e
    st += delta * ratio
    # print(st)

print('\n', cnt_p, cnt_n)
print('\n', f'平均每周期利润{round(total/turns/100000000, 5)}e')
print('\n', f'最大亏损{round(t_min/1000000, 3)}m  最大盈利{round(t_max/1000000, 3)}m')
print('\n', f'最终钱{round(st/100000000, 3)}e')

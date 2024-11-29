from .overload import overload_count
from .kusa_envelope import handout
from .lianhao import lianhao_count
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name='生草系统助手',
    description='帮助你使用生草系统',
    usage='一些辅助小功能',
    type='application',
    extra={
        'menu_data': [
            {
                'func': '连号计算',
                'trigger_method': '连号计算',
                'trigger_condition': '用户指令',
                'brief_des': '计算特定生草区间的连号概率',
                'detail_des': '/连号计算 num1 num2\n'
                              '# 计算当生草量为num1~num2时，连号各结果的概率\n'
                              '/连号计算 num1 num2 num3 y/n num4\n'
                              '# 五个参数分别为: 信息员等级(4~8), 草地数量(1~400), 生草数量等级(0~4), 是否启用沼气(y/n), 草种相关影响(1~20)'
            },
            {
                'func': '过载计算',
                'trigger_method': '过载计算',
                'trigger_condition': '用户指令',
                'brief_des': '计算特定生草区间的过载概率',
                'detail_des': '/过载计算 num1 num2\n'
                              '# 计算当生草量为num1~num2时，过载结果为各时段的概率'
            },
            {
                'func': '发草包',
                'trigger_method': '发草包',
                'trigger_condition': '用户指令',
                'brief_des': '发出拼手气草包',
                'detail_des': '/发草包 num  # num为草包的个数, num>=3'
            },
            {
                'func': '抢草包',
                'trigger_method': '抢草包',
                'trigger_condition': '用户指令',
                'brief_des': '抢群内所有拼手气草包',
                'detail_des': '/抢草包'
            },
        ],
        'menu_template': 'default'
    }
)

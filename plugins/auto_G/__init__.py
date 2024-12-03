from .bank import plugin_config
from .stastic import plugin_config
from .G_follow import plugin_config
from .G_free import plugin_config
from .G_control import plugin_config
from .G_bottom_fishing import plugin_config
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name='生草系统银行',
    description='自动化银行服务',
    usage='草行 3.0',
    type='application',
    extra={
        'menu_data': [
            {
                'func': '利率',
                'trigger_method': '草利率',
                'trigger_condition': '用户指令',
                'brief_des': '查看利率方面的计算方式',
                'detail_des': 'TODO'
            },
            {
                'func': '查账',
                'trigger_method': '草盈亏',
                'trigger_condition': '用户指令',
                'brief_des': '查看银行本周期的投资盈亏',
                'detail_des': 'TODO'
            },
            {
                'func': '账户',
                'trigger_method': '草账户',
                'trigger_condition': '用户指令',
                'brief_des': '查看自己账户信息',
                'detail_des': 'TODO'
            },
            {
                'func': '存款',
                'trigger_method': '草存入',
                'trigger_condition': '用户指令',
                'brief_des': '开始存草流程',
                'detail_des': 'TODO'
            },
            {
                'func': '取款',
                'trigger_method': '草取出',
                'trigger_condition': '用户指令',
                'brief_des': '立即取出草',
                'detail_des': 'TODO'
            },
            {
                'func': '大额取款',
                'trigger_method': '草预约取出',
                'trigger_condition': '用户指令',
                'brief_des': '预约在G周期结束时取出大额草',
                'detail_des': 'TODO'
            },
            {
                'func': '审批',
                'trigger_method': '草审批',
                'trigger_condition': '用户指令',
                'brief_des': '审批用户当前工厂情况以服务后续',
                'detail_des': 'TODO'
            },
            {
                'func': '贷款',
                'trigger_method': '草借款',
                'trigger_condition': '用户指令',
                'brief_des': '立刻从草行借草',
                'detail_des': 'TODO'
            },
            {
                'func': '还款',
                'trigger_method': '草还款',
                'trigger_condition': '用户指令',
                'brief_des': '开始自助还款流程',
                'detail_des': 'TODO'
            },
            {
                'func': '提线木偶',
                'trigger_method': 'G帮助',
                'trigger_condition': '用户指令',
                'brief_des': '查看给用户控制炒G相关',
                'detail_des': 'TODO'
            },
            {
                'func': '分红',
                'trigger_method': '分红',
                'trigger_condition': '用户指令',
                'brief_des': '获取银行各种业务的分红',
                'detail_des': 'TODO'
            },
            {
                'func': '看存款',
                'trigger_method': '查看草存款',
                'trigger_condition': '超管指令',
                'brief_des': '查看所有用户存款',
                'detail_des': 'TODO'
            },
            {
                'func': '看贷款',
                'trigger_method': '查看草贷款',
                'trigger_condition': '超管指令',
                'brief_des': '查看所有用户贷款',
                'detail_des': 'TODO'
            },
            {
                'func': '看账户',
                'trigger_method': '查看草账户',
                'trigger_condition': '超管指令',
                'brief_des': '查看某用户账户信息',
                'detail_des': 'TODO'
            },
            {
                'func': '记账',
                'trigger_method': '草记账',
                'trigger_condition': '超管指令',
                'brief_des': '手动发贷款时给用户记账',
                'detail_des': 'TODO'
            },
            {
                'func': '销账',
                'trigger_method': '草销账',
                'trigger_condition': '超管指令',
                'brief_des': '手动收还款时给用户销账',
                'detail_des': 'TODO'
            },
        ],
        'menu_template': 'default'
    }
)

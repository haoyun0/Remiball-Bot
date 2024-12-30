# 蕾米球Bot

名为"蕾米球"的QQBot，采用Python编写，基于NoneBot2构建。

蕾米球当前在以下项目的基础上构建：

https://github.com/nonebot/nonebot2

https://github.com/NapNeko/NapCatQQ

## 插件介绍

auto_kusa: 生草系统自动生草

kusa_helper: 生草系统小助手

auto_G: 生草系统银行、测G相关

params: 自己写的各种方便写代码的函数

下面为我自己记录如何使用nonebot2的

plugins.params.rule，自己写rule

plugins.params.permission，自己写permission

plugins.params.hook_bot，hook钩子函数使用，实例为只让一个bot响应插件，并让其他bot只响应排除列表的插件

plugins.params.message_api，整合了onebot11发消息api，自己写的插件都通过这个api发消息，后续可用于统计发消息数

plugins.auto_G.bank，功能最全的一集，on_command, on_regex, 依赖注入（维护状态不允许响应/一条消息即使是同优先级也只被响应一次），
定时任务，config配置文件使用，rule和permission的使用，临时添加事件响应器。

## 声明

本项目仅供学习交流使用，不得用于非法用途。

## 友链

小石子的除草器bot(生草系统): https://github.com/BouncyKoishi/ChuCaoQi-Bot

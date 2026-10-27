# more-itertools：假值自定义异常被默认异常覆盖

修复one和only：用户提供的too_short/too_long异常即使布尔值为False也必须被抛出。指定自定义too_long时不要构造含元素repr的默认消息，避免元素的repr错误覆盖自定义异常。保留单元素返回、one空输入异常和only空输入default行为。

MIT-licensed function excerpt. See LICENSE.md.

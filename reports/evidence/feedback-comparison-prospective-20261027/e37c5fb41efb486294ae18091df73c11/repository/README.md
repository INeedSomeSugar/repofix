# 事件游标分页的同序号边界

修复project.core.page(events, limit, after=None)。events是可迭代事件字典，sequence为整数，event_id为唯一字符串。按(sequence,event_id)升序分页；after是二元素序列，严格返回大于该复合键的事件，游标不必对应已有事件。limit须为1至100的整数且不能是bool，否则ValueError。返回{'items':列表,'next_cursor':游标或None}；仅还有后续记录时next_cursor为本页末条的[sequence,event_id]，否则None。输入为空或游标之后无记录时返回空items和None。不得修改输入列表或事件；每个返回事件须为浅拷贝。

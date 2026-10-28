# 整数金额按权重分配与余数守恒

修复project.core.allocate_cents(total, weights)。total是任意大小的整数分金额，可为负且不能为bool；weights是可迭代的非负整数权重，不接受bool。使用最大余数法：先按abs(total)比例向下分配，再按精确余数从大到小补1分，余数相同按原始索引升序。最后统一恢复total符号，返回与权重顺序一致的整数列表，合计必须等于total。非空weights的权重总和须大于0。空weights仅当total=0时返回[]，否则ValueError。其他无效类型或负权重也抛ValueError，不修改输入，整个计算不得使用浮点近似。

# more-itertools：maxsplit=0时空输入产生额外空分组

修复split_before、split_after、split_when：空输入在maxsplit=0时也应产生零个分组；非空输入在maxsplit=0时仍产生包含全部内容的一组。保留各自原有拆分位置、惰性迭代与maxsplit语义。

MIT-licensed function excerpt. See LICENSE.md.

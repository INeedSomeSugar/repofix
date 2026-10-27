# more-itertools：迭代期间的TypeError被误当作标量

修复value_chain：字符串和bytes仍原样输出；不可迭代参数作为标量；已经开始消费的迭代器若抛出TypeError，必须向调用者传播，不能吞掉错误或输出该迭代器。

MIT-licensed function excerpt. See LICENSE.md.

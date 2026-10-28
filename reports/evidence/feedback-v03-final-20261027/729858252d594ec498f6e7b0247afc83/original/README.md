# 滑动平均窗口边界

修复 project.core.rolling_average(values, window)。只返回完整窗口的平均值；例如 [1,2,3,4]、window=2 得到 [1.5,2.5,3.5]。window 必须是正整数且不能是 bool，否则抛出 ValueError。窗口大于输入长度或输入为空时返回 []，不能修改输入列表。

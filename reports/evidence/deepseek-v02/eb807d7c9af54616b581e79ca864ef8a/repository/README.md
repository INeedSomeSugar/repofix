# 跨文件区间合并

修复 project.core.merge_intervals(intervals)。输入为 start <= end 的闭区间二元列表。合并重叠及端点相接的区间，按起点排序返回新列表；不允许修改输入或复用输入的子列表。空输入返回 []，要检查 project/utils.py 中的重叠判断。

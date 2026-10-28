# 库存批量变更的原子性与版本检查

修复project.core.apply_batch(stock, versions, changes)。stock和versions是已有SKU到非负整数库存和版本的字典。changes是可迭代字典，每项含sku、delta、expected_version。按顺序应用；同SKU后续操作须基于前一次递增后的版本检查。delta为整数（可为0），expected_version为非负整数，两者不接受bool；无效参数、版本不匹配或变更后库存负数抛ValueError，未知sku抛KeyError。每项成功变更版本加1。成功返回(new_stock,new_versions)，两字典都须为新对象；无论中途失败还是成功，均不得修改任何输入字典或changes中的对象。空变更也返回副本。

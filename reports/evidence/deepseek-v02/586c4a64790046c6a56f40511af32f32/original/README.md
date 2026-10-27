# 词频排序与参数校验

修复 project.core.top_words(text,k)。将连续 ASCII 英文字母 a-z/A-Z 视为一个词，忽略大小写，按出现次数降序、同频时按词的字典序升序，返回前 k 个 (word,count) 元组。k=0 或无词时返回 []。k 为负数、bool 或非整数时抛出 ValueError。

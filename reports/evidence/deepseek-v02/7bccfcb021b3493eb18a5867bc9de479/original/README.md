# 缓存过期与假值

修复 project.core.TTLCache。set(key,value,ttl,now) 使用调用方提供的时间；ttl<0 抛出 ValueError。get(key,now,default=None) 在 now >= 设置时间+ttl 时过期并返回 default；未过期的 0、False、空字符串和 None 都必须原样返回。重新 set 应覆盖旧值和过期时间。

---
inclusion: always
---

# 禁用API请求缓存

## 规则

**所有客户端API请求必须禁用缓存。**

## 原因

- API缓存会导致数据不一致问题
- 用户操作后看不到最新数据
- 增加调试难度
- 在管理后台场景下，数据实时性比性能更重要

## 实现方式

### 前端请求拦截器

在 `admin-web/src/api/request.js` 中：

```javascript
// ❌ 不要启用GET请求缓存
// if (config.method === 'get' && config.cache !== false) {
//   const cached = requestCache.get(config.url, config.params)
//   if (cached) {
//     return Promise.reject({ __cached: true, data: cached })
//   }
// }

// ❌ 不要缓存响应结果
// if (response.config.method === 'get' && response.config.cache !== false) {
//   requestCache.set(response.config.url, response.config.params, response.data)
// }
```

### 如果需要性能优化

- 使用后端缓存（Redis）而不是前端缓存
- 使用分页减少数据量
- 使用虚拟滚动优化长列表
- 使用防抖/节流控制请求频率

## 适用范围

- 管理后台的所有API请求
- C端用户界面的写操作后的查询请求
- 实时性要求高的数据查询

## 例外情况

如果确实需要缓存（如静态配置数据），必须：
1. 明确标注缓存时间
2. 提供手动刷新机制
3. 在相关数据变更后清除缓存

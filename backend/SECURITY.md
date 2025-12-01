# 安全加固文档

## 概述

本文档描述了企业内部短视频平台的安全加固措施，包括API安全防护、SQL注入防护、XSS防护、CSRF防护和敏感数据加密。

## 已实施的安全措施

### 1. API安全防护

#### 限流保护
- **实现位置**: `backend/app/utils/rate_limiter.py`
- **功能**: 防止API滥用和DDoS攻击
- **配置**:
  - 默认限制: 100请求/分钟
  - 可通过环境变量配置
  - 支持基于IP和用户ID的限流

#### 认证和授权
- **JWT Token认证**: 所有API请求需要有效的JWT token
- **Token过期时间**: 24小时（可配置）
- **权限检查**: 基于用户角色的权限控制

### 2. SQL注入防护

#### 参数化查询
- **实现**: 使用SQLAlchemy ORM，所有查询都是参数化的
- **验证器**: `SecurityValidator.validate_sql_injection()`
- **防护措施**:
  - 检测危险SQL关键词
  - 过滤特殊字符
  - 转义单引号

#### 输入验证
```python
from app.utils.security import validate_input

@app.post("/api/comment")
@validate_input(sql_injection=True)
async def create_comment(text: str):
    # 自动验证输入，防止SQL注入
    pass
```

### 3. XSS防护

#### HTML实体编码
- **实现位置**: `backend/app/utils/security.py`
- **功能**: `SecurityValidator.sanitize_html()`
- **应用场景**:
  - 用户评论
  - 内容描述
  - 用户输入的所有文本

#### 内容安全策略（CSP）
- **响应头**: `Content-Security-Policy: default-src 'self'`
- **防护**: 防止内联脚本执行

### 4. CSRF防护

#### CSRF Token
- **实现位置**: `backend/app/utils/security.py`
- **功能**: `CSRFProtection`
- **使用方法**:
  1. 生成token: `CSRFProtection.generate_token()`
  2. 验证token: `CSRFProtection.validate_token()`

#### 同源策略
- **CORS配置**: 生产环境限制允许的域名
- **Referer检查**: 验证请求来源

### 5. 敏感数据加密

#### 字段级加密
- **实现位置**: `backend/app/utils/encryption.py`
- **加密算法**: Fernet (对称加密)
- **密钥派生**: PBKDF2 with SHA256

#### 加密字段示例
```python
from app.utils.encryption import FieldEncryptionMixin

class User(Base, FieldEncryptionMixin):
    _encrypted_fields = ['phone', 'email']
    
    phone = Column(String(100))
    email = Column(String(200))
```

#### 密码哈希
- **算法**: PBKDF2-HMAC-SHA256
- **迭代次数**: 100,000
- **盐值**: 随机生成，每个密码独立

### 6. 安全响应头

所有API响应都包含以下安全头：

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 7. 数据库安全

#### 连接安全
- **SSL/TLS**: 生产环境强制使用加密连接
- **连接池**: 限制最大连接数，防止资源耗尽
- **连接回收**: 定期回收空闲连接

#### 权限最小化
- **数据库用户**: 只授予必要的权限
- **读写分离**: 使用只读副本处理查询

### 8. 文件上传安全

#### 文件类型验证
- **白名单**: 只允许特定格式（MP4, MOV, AVI）
- **MIME类型检查**: 验证文件真实类型
- **文件大小限制**: 防止大文件攻击

#### 路径遍历防护
- **验证器**: `SecurityValidator.validate_file_path()`
- **防护**: 检测 `..`, `~`, `/etc/` 等危险路径

### 9. 日志和监控

#### 安全日志
- **记录内容**:
  - 登录尝试（成功和失败）
  - 权限拒绝
  - SQL注入尝试
  - XSS攻击尝试
  - 异常API调用

#### 性能监控
- **慢请求检测**: 超过1秒的请求
- **异常流量检测**: 异常高的请求频率
- **错误率监控**: API错误率超过阈值告警

## 配置建议

### 环境变量

```bash
# JWT密钥（必须修改）
JWT_SECRET_KEY=your-secret-key-here

# 加密密钥（必须修改）
ENCRYPTION_KEY=your-encryption-key-here

# 数据库连接（使用SSL）
DATABASE_URL=mysql+aiomysql://user:pass@host:3306/db?ssl=true

# 限流配置
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# CORS配置（生产环境）
CORS_ORIGINS=https://your-domain.com
```

### 生产环境检查清单

- [ ] 修改所有默认密钥和密码
- [ ] 启用HTTPS（强制）
- [ ] 配置CORS白名单
- [ ] 启用数据库SSL连接
- [ ] 配置防火墙规则
- [ ] 启用日志记录
- [ ] 配置监控告警
- [ ] 定期备份数据库
- [ ] 定期更新依赖包
- [ ] 进行安全审计

## 安全测试

### 渗透测试工具

1. **OWASP ZAP**: Web应用安全扫描
2. **SQLMap**: SQL注入测试
3. **Burp Suite**: 综合安全测试

### 测试场景

1. **SQL注入测试**
   - 在所有输入字段尝试SQL注入
   - 测试参数化查询是否有效

2. **XSS测试**
   - 在评论、描述等字段注入脚本
   - 验证HTML实体编码是否生效

3. **CSRF测试**
   - 尝试跨站请求伪造
   - 验证token验证机制

4. **认证测试**
   - 测试token过期处理
   - 测试权限检查

5. **限流测试**
   - 发送大量请求测试限流
   - 验证429响应

## 安全更新

### 依赖包更新

定期检查和更新依赖包：

```bash
# 检查过期包
pip list --outdated

# 更新包
pip install --upgrade package-name

# 检查安全漏洞
pip-audit
```

### 安全公告订阅

- Python安全公告: https://www.python.org/news/security/
- FastAPI安全公告: https://github.com/tiangolo/fastapi/security
- SQLAlchemy安全公告: https://www.sqlalchemy.org/security.html

## 应急响应

### 安全事件处理流程

1. **发现**: 通过监控或报告发现安全事件
2. **评估**: 评估影响范围和严重程度
3. **隔离**: 隔离受影响的系统或用户
4. **修复**: 修复漏洞或问题
5. **恢复**: 恢复正常服务
6. **总结**: 编写事件报告，改进安全措施

### 联系方式

- **安全团队邮箱**: security@company.com
- **紧急联系人**: [姓名] [电话]

## 合规性

### 数据保护

- **个人信息保护**: 符合《个人信息保护法》
- **数据安全**: 符合《数据安全法》
- **网络安全**: 符合《网络安全法》

### 审计

- **定期审计**: 每季度进行安全审计
- **审计日志**: 保留至少6个月
- **合规报告**: 每年提交合规报告

## 参考资料

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/faq/security.html)

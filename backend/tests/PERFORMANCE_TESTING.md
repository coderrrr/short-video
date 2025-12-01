# 性能测试指南

## 概述

本项目使用 Locust 进行性能测试和负载测试。性能测试脚本位于 `backend/tests/locustfile.py`。

## 性能目标

- **API响应时间**: < 2秒
- **错误率**: < 1%
- **并发用户数**: >= 100

## 安装依赖

```bash
conda run -n short-video pip install locust
```

## 运行性能测试

### 1. 启动后端服务

首先确保后端服务正在运行：

```bash
# 使用Docker Compose启动
docker-compose up -d

# 或者直接运行后端
cd backend
conda run -n short-video uvicorn app.main:app --reload
```

### 2. 运行Locust Web界面

使用Web界面进行交互式测试：

```bash
cd backend
conda run -n short-video locust -f tests/locustfile.py --host=http://localhost:8000
```

然后在浏览器中打开 http://localhost:8089，设置：
- **Number of users**: 100（并发用户数）
- **Spawn rate**: 10（每秒启动的用户数）
- **Host**: http://localhost:8000

点击 "Start swarming" 开始测试。

### 3. 运行无头模式（命令行）

适合CI/CD集成：

```bash
cd backend
conda run -n short-video locust -f tests/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless \
  --html performance_report.html
```

参数说明：
- `--users 100`: 模拟100个并发用户
- `--spawn-rate 10`: 每秒启动10个用户
- `--run-time 5m`: 运行5分钟
- `--headless`: 无头模式（不启动Web界面）
- `--html performance_report.html`: 生成HTML报告

### 4. 分布式负载测试

如需更高的负载，可以使用分布式模式：

**主节点（Master）：**
```bash
conda run -n short-video locust -f tests/locustfile.py \
  --host=http://localhost:8000 \
  --master
```

**工作节点（Worker）：**
```bash
# 在其他机器或终端运行
conda run -n short-video locust -f tests/locustfile.py \
  --host=http://localhost:8000 \
  --worker \
  --master-host=<master-ip>
```

## 测试场景

### 1. VideoLearningPlatformUser（普通用户）

模拟最常见的用户行为：
- **浏览推荐内容**（权重：10）- 最频繁
- **查看内容详情**（权重：7）
- **按分类浏览**（权重：5）
- **点赞内容**（权重：4）
- **搜索内容**（权重：3）
- **收藏内容**（权重：3）
- **评论内容**（权重：2）
- **查看个人资料**（权重：2）
- **查看我的收藏**（权重：2）
- **查看学习进度**（权重：1）

### 2. ContentCreatorUser（内容创作者）

模拟创作者行为（较少但更重）：
- **查看我的发布**（权重：5）
- **查看草稿**（权重：3）
- **创建草稿**（权重：1）

### 3. AdminUser（管理员）

模拟管理员行为（最少）：
- **查看审核队列**（权重：5）
- **查看内容分析**（权重：3）
- **查看用户互动**（权重：2）

## 用户比例配置

默认情况下，Locust会平均分配用户类型。如需自定义比例，可以在locustfile.py中设置：

```python
class VideoLearningPlatformUser(HttpUser):
    weight = 10  # 普通用户占比最高

class ContentCreatorUser(HttpUser):
    weight = 2   # 创作者占比较低

class AdminUser(HttpUser):
    weight = 1   # 管理员占比最低
```

## 性能指标解读

### 关键指标

1. **响应时间（Response Time）**
   - Average: 平均响应时间
   - Median: 中位数响应时间
   - 95th percentile: 95%的请求响应时间
   - 99th percentile: 99%的请求响应时间

2. **吞吐量（Throughput）**
   - RPS (Requests Per Second): 每秒请求数
   - Total Requests: 总请求数

3. **错误率（Failure Rate）**
   - Failures: 失败请求数
   - Failure Ratio: 失败率百分比

### 性能瓶颈识别

如果性能测试未达到目标，检查以下方面：

1. **数据库查询优化**
   - 检查慢查询日志
   - 添加必要的索引
   - 优化复杂查询

2. **缓存策略**
   - 增加Redis缓存
   - 实现查询结果缓存
   - 使用CDN缓存静态资源

3. **应用层优化**
   - 异步处理耗时操作
   - 使用连接池
   - 减少不必要的数据库查询

4. **基础设施扩展**
   - 增加应用服务器实例
   - 使用负载均衡
   - 升级数据库实例规格

## 持续集成

在CI/CD流程中集成性能测试：

```yaml
# .github/workflows/performance-test.yml
name: Performance Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  performance-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install locust
    
    - name: Start services
      run: |
        docker-compose up -d
        sleep 30  # 等待服务启动
    
    - name: Run performance test
      run: |
        cd backend
        locust -f tests/locustfile.py \
          --host=http://localhost:8000 \
          --users 50 \
          --spawn-rate 5 \
          --run-time 2m \
          --headless \
          --html performance_report.html
    
    - name: Upload report
      uses: actions/upload-artifact@v2
      with:
        name: performance-report
        path: backend/performance_report.html
```

## 故障排查

### 常见问题

1. **连接被拒绝**
   - 确保后端服务正在运行
   - 检查端口是否正确
   - 检查防火墙设置

2. **认证失败**
   - 检查测试用户凭据
   - 确保认证端点正确
   - 验证token格式

3. **高错误率**
   - 检查应用日志
   - 验证API端点是否正确
   - 检查数据库连接

4. **响应时间过长**
   - 检查数据库查询性能
   - 验证网络延迟
   - 检查服务器资源使用情况

## 最佳实践

1. **逐步增加负载**
   - 从小负载开始（10-20用户）
   - 逐步增加到目标负载
   - 观察系统行为变化

2. **监控系统资源**
   - CPU使用率
   - 内存使用率
   - 磁盘I/O
   - 网络带宽

3. **定期执行测试**
   - 在每次重大更新后运行
   - 建立性能基线
   - 跟踪性能趋势

4. **真实场景模拟**
   - 使用真实的用户行为模式
   - 模拟不同的用户类型
   - 考虑峰值时段的负载

## 参考资源

- [Locust官方文档](https://docs.locust.io/)
- [性能测试最佳实践](https://docs.locust.io/en/stable/writing-a-locustfile.html)
- [分布式负载测试](https://docs.locust.io/en/stable/running-distributed.html)

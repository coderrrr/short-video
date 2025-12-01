<template>
  <div class="dashboard">
    <h2 class="page-title">数据概览</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #ecf5ff; color: #409eff;">
              <el-icon :size="32"><VideoCamera /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_contents || 0 }}</div>
              <div class="stat-label">总视频数</div>
              <div class="stat-change" v-if="stats.today_new_contents">
                <span class="change-value positive">+{{ stats.today_new_contents }}</span>
                <span class="change-label">今日新增</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fef0f0; color: #f56c6c;">
              <el-icon :size="32"><Star /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_likes || 0 }}</div>
              <div class="stat-label">总点赞数</div>
              <div class="stat-change" v-if="stats.today_likes">
                <span class="change-value positive">+{{ stats.today_likes }}</span>
                <span class="change-label">今日点赞</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f0f9ff; color: #67c23a;">
              <el-icon :size="32"><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_favorites || 0 }}</div>
              <div class="stat-label">总收藏数</div>
              <div class="stat-change" v-if="stats.today_favorites">
                <span class="change-value positive">+{{ stats.today_favorites }}</span>
                <span class="change-label">今日收藏</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c;">
              <el-icon :size="32"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_comments || 0 }}</div>
              <div class="stat-label">总评论数</div>
              <div class="stat-change" v-if="stats.today_comments">
                <span class="change-value positive">+{{ stats.today_comments }}</span>
                <span class="change-label">今日评论</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表和排行榜 -->
    <el-row :gutter="20" class="charts-row">
      <!-- 热门视频排行 -->
      <el-col :xs="24" :md="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">热门视频 TOP 10</span>
              <el-select v-model="topContentMetric" size="small" style="width: 120px" @change="loadTopContents">
                <el-option label="观看量" value="views" />
                <el-option label="点赞数" value="likes" />
                <el-option label="收藏数" value="favorites" />
              </el-select>
            </div>
          </template>
          <div v-loading="topContentsLoading" class="ranking-list">
            <div v-if="topContents.length === 0" class="empty-data">暂无数据</div>
            <div v-else>
              <div v-for="(item, index) in topContents" :key="item.id" class="ranking-item">
                <div class="ranking-number" :class="{ 'top-three': index < 3 }">
                  {{ index + 1 }}
                </div>
                <div class="ranking-cover">
                  <el-image :src="item.cover_url" fit="cover" />
                </div>
                <div class="ranking-info">
                  <div class="ranking-title">{{ item.title }}</div>
                  <div class="ranking-meta">
                    <span>{{ item.creator?.name }}</span>
                    <span class="separator">·</span>
                    <span>{{ formatDate(item.created_at) }}</span>
                  </div>
                </div>
                <div class="ranking-value">
                  {{ formatNumber(item[topContentMetric === 'views' ? 'view_count' : topContentMetric === 'likes' ? 'like_count' : 'favorite_count']) }}
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 活跃用户排行 -->
      <el-col :xs="24" :md="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">活跃用户 TOP 10</span>
              <el-select v-model="topUserMetric" size="small" style="width: 120px" @change="loadTopUsers">
                <el-option label="发布数" value="contents" />
                <el-option label="获赞数" value="likes" />
                <el-option label="粉丝数" value="followers" />
              </el-select>
            </div>
          </template>
          <div v-loading="topUsersLoading" class="ranking-list">
            <div v-if="topUsers.length === 0" class="empty-data">暂无数据</div>
            <div v-else>
              <div v-for="(item, index) in topUsers" :key="item.id" class="ranking-item">
                <div class="ranking-number" :class="{ 'top-three': index < 3 }">
                  {{ index + 1 }}
                </div>
                <div class="ranking-avatar">
                  <el-avatar :size="40" :src="item.avatar_url">
                    {{ item.name?.charAt(0) }}
                  </el-avatar>
                </div>
                <div class="ranking-info">
                  <div class="ranking-title">
                    {{ item.name }}
                    <el-tag v-if="item.is_kol" size="small" type="warning" style="margin-left: 8px">KOL</el-tag>
                  </div>
                  <div class="ranking-meta">
                    {{ item.department }} · {{ item.position }}
                  </div>
                </div>
                <div class="ranking-value">
                  {{ formatNumber(item[topUserMetric === 'contents' ? 'content_count' : topUserMetric === 'likes' ? 'total_likes' : 'followers_count']) }}
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card small">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_users || 0 }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card small">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_kols || 0 }}</div>
              <div class="stat-label">KOL用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card small">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_views || 0 }}</div>
              <div class="stat-label">总观看次数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card small">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_shares || 0 }}</div>
              <div class="stat-label">总分享次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera, Star, Collection, ChatDotRound } from '@element-plus/icons-vue'
import { getDashboardStats, getTopContents, getTopUsers } from '../api/dashboard'

// 统计数据
const stats = reactive({
  total_contents: 0,
  today_new_contents: 0,
  total_likes: 0,
  today_likes: 0,
  total_favorites: 0,
  today_favorites: 0,
  total_comments: 0,
  today_comments: 0,
  total_users: 0,
  total_kols: 0,
  total_views: 0,
  total_shares: 0
})

// 热门内容
const topContents = ref([])
const topContentsLoading = ref(false)
const topContentMetric = ref('views')

// 活跃用户
const topUsers = ref([])
const topUsersLoading = ref(false)
const topUserMetric = ref('contents')

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await getDashboardStats()
    Object.assign(stats, response)
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  }
}

// 加载热门内容
const loadTopContents = async () => {
  topContentsLoading.value = true
  try {
    const response = await getTopContents({
      metric: topContentMetric.value,
      limit: 10
    })
    topContents.value = response.items || []
  } catch (error) {
    console.error('加载热门内容失败:', error)
    ElMessage.error('加载热门内容失败')
  } finally {
    topContentsLoading.value = false
  }
}

// 加载活跃用户
const loadTopUsers = async () => {
  topUsersLoading.value = true
  try {
    const response = await getTopUsers({
      metric: topUserMetric.value,
      limit: 10
    })
    topUsers.value = response.items || []
  } catch (error) {
    console.error('加载活跃用户失败:', error)
    ElMessage.error('加载活跃用户失败')
  } finally {
    topUsersLoading.value = false
  }
}

// 格式化数字
const formatNumber = (num) => {
  if (!num) return 0
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit'
  })
}

// 初始化
onMounted(() => {
  loadStats()
  loadTopContents()
  loadTopUsers()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.page-title {
  margin: 0 0 20px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-card.small {
  margin-bottom: 0;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-change {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.change-value {
  font-weight: 600;
}

.change-value.positive {
  color: #67c23a;
}

.change-label {
  color: #909399;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.ranking-list {
  min-height: 400px;
}

.empty-data {
  text-align: center;
  color: #909399;
  padding: 60px 0;
  font-size: 14px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.ranking-item:hover {
  background-color: #f5f7fa;
}

.ranking-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #f5f7fa;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.ranking-number.top-three {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #fff;
}

.ranking-cover {
  width: 60px;
  height: 40px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}

.ranking-cover .el-image {
  width: 100%;
  height: 100%;
}

.ranking-avatar {
  flex-shrink: 0;
}

.ranking-info {
  flex: 1;
  min-width: 0;
}

.ranking-title {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.ranking-meta {
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.separator {
  margin: 0 4px;
}

.ranking-value {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .stat-icon {
    width: 48px;
    height: 48px;
  }

  .stat-value {
    font-size: 24px;
  }

  .ranking-cover {
    width: 48px;
    height: 32px;
  }
}
</style>

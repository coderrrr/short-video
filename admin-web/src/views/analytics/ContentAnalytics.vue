<template>
  <div class="content-analytics">
    <el-card class="summary-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>内容性能概览</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">总内容数</div>
            <div class="stat-value">{{ summary.total_contents || 0 }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">总观看次数</div>
            <div class="stat-value">{{ formatNumber(summary.total_views) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">总点赞数</div>
            <div class="stat-value">{{ formatNumber(summary.total_likes) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">总收藏数</div>
            <div class="stat-value">{{ formatNumber(summary.total_favorites) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="content-list-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>内容性能列表</span>
          <div class="header-actions">
            <el-select
              v-model="sortBy"
              placeholder="排序字段"
              style="width: 150px; margin-right: 10px"
              @change="handleSortChange"
            >
              <el-option label="观看次数" value="view_count" />
              <el-option label="完播次数" value="completion_count" />
              <el-option label="点赞数" value="like_count" />
              <el-option label="收藏数" value="favorite_count" />
              <el-option label="完播率" value="completion_rate" />
            </el-select>
            <el-select
              v-model="order"
              placeholder="排序方向"
              style="width: 120px; margin-right: 10px"
              @change="handleSortChange"
            >
              <el-option label="降序" value="desc" />
              <el-option label="升序" value="asc" />
            </el-select>
            <el-button type="primary" @click="handleExport">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="contentList"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="title" label="内容标题" min-width="200" />
        <el-table-column prop="creator_name" label="创作者" width="120" />
        <el-table-column prop="view_count" label="观看次数" width="100" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.view_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="completion_count" label="完播次数" width="100" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.completion_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="unique_viewers" label="独立观众" width="100" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.unique_viewers) }}
          </template>
        </el-table-column>
        <el-table-column prop="like_count" label="点赞数" width="90" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.like_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="favorite_count" label="收藏数" width="90" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.favorite_count) }}
          </template>
        </el-table-column>
        <el-table-column prop="completion_rate" label="完播率" width="100" align="right">
          <template #default="{ row }">
            {{ formatPercentage(row.completion_rate) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="viewDetails(row.content_id)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 详细分析对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="内容详细分析"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-loading="detailLoading" class="detail-content">
        <el-descriptions :column="2" border v-if="detailData">
          <el-descriptions-item label="内容标题">
            {{ detailData.title }}
          </el-descriptions-item>
          <el-descriptions-item label="创作者">
            {{ detailData.creator_name }}
          </el-descriptions-item>
          <el-descriptions-item label="发布时间">
            {{ formatDateTime(detailData.published_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="内容时长">
            {{ formatDuration(detailData.duration) }}
          </el-descriptions-item>
          <el-descriptions-item label="观看次数">
            {{ formatNumber(detailData.view_count) }}
          </el-descriptions-item>
          <el-descriptions-item label="完播次数">
            {{ formatNumber(detailData.completion_count) }}
          </el-descriptions-item>
          <el-descriptions-item label="独立观众数">
            {{ formatNumber(detailData.unique_viewers) }}
          </el-descriptions-item>
          <el-descriptions-item label="完播率">
            {{ formatPercentage(detailData.completion_rate) }}
          </el-descriptions-item>
          <el-descriptions-item label="点赞数">
            {{ formatNumber(detailData.like_count) }}
          </el-descriptions-item>
          <el-descriptions-item label="收藏数">
            {{ formatNumber(detailData.favorite_count) }}
          </el-descriptions-item>
          <el-descriptions-item label="评论数">
            {{ formatNumber(detailData.comment_count) }}
          </el-descriptions-item>
          <el-descriptions-item label="分享数">
            {{ formatNumber(detailData.share_count) }}
          </el-descriptions-item>
          <el-descriptions-item label="平均观看时长">
            {{ formatDuration(detailData.avg_watch_duration) }}
          </el-descriptions-item>
          <el-descriptions-item label="平均观看进度">
            {{ formatPercentage(detailData.avg_watch_progress) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 数据图表 -->
        <div class="charts-container" v-if="detailData">
          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="12">
              <el-card shadow="never">
                <template #header>
                  <span>观看趋势</span>
                </template>
                <div ref="viewTrendChart" style="height: 300px"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card shadow="never">
                <template #header>
                  <span>互动数据分布</span>
                </template>
                <div ref="interactionChart" style="height: 300px"></div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import {
  getContentAnalyticsSummary,
  getContentDetailedAnalytics,
  exportAnalyticsReport
} from '@/api/analytics'

// 数据
const loading = ref(false)
const summary = ref({})
const contentList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const sortBy = ref('view_count')
const order = ref('desc')

// 详情对话框
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)
const viewTrendChart = ref(null)
const interactionChart = ref(null)
let viewTrendChartInstance = null
let interactionChartInstance = null

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const response = await getContentAnalyticsSummary({
      page: currentPage.value,
      page_size: pageSize.value,
      sort_by: sortBy.value,
      order: order.value
    })
    
    summary.value = response.summary || {}
    contentList.value = response.contents || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载内容分析数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 格式化数字
const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString()
}

// 格式化百分比
const formatPercentage = (value) => {
  if (value === null || value === undefined) return '0%'
  return `${(value * 100).toFixed(1)}%`
}

// 格式化时长（秒转为分:秒）
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 排序变化
const handleSortChange = () => {
  currentPage.value = 1
  loadData()
}

// 页码变化
const handlePageChange = (page) => {
  currentPage.value = page
  loadData()
}

// 每页数量变化
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadData()
}

// 行点击
const handleRowClick = (row) => {
  viewDetails(row.content_id)
}

// 查看详情
const viewDetails = async (contentId) => {
  detailDialogVisible.value = true
  detailLoading.value = true
  
  try {
    const response = await getContentDetailedAnalytics(contentId)
    detailData.value = response
    
    // 等待DOM更新后初始化图表
    await nextTick()
    initCharts()
  } catch (error) {
    console.error('加载详细分析失败:', error)
    ElMessage.error('加载详细分析失败')
  } finally {
    detailLoading.value = false
  }
}

// 初始化图表
const initCharts = () => {
  if (!detailData.value) return
  
  // 观看趋势图表
  if (viewTrendChart.value) {
    if (viewTrendChartInstance) {
      viewTrendChartInstance.dispose()
    }
    viewTrendChartInstance = echarts.init(viewTrendChart.value)
    
    const viewTrendOption = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: detailData.value.view_trend?.dates || []
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '观看次数',
          type: 'line',
          data: detailData.value.view_trend?.counts || [],
          smooth: true,
          itemStyle: {
            color: '#409EFF'
          }
        }
      ]
    }
    viewTrendChartInstance.setOption(viewTrendOption)
  }
  
  // 互动数据分布图表
  if (interactionChart.value) {
    if (interactionChartInstance) {
      interactionChartInstance.dispose()
    }
    interactionChartInstance = echarts.init(interactionChart.value)
    
    const interactionOption = {
      tooltip: {
        trigger: 'item'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '互动类型',
          type: 'pie',
          radius: '50%',
          data: [
            { value: detailData.value.like_count || 0, name: '点赞' },
            { value: detailData.value.favorite_count || 0, name: '收藏' },
            { value: detailData.value.comment_count || 0, name: '评论' },
            { value: detailData.value.share_count || 0, name: '分享' }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
    interactionChartInstance.setOption(interactionOption)
  }
}

// 导出报告
const handleExport = async () => {
  try {
    ElMessage.info('正在生成报告...')
    
    // 获取所有选中的内容ID（这里导出当前页的所有内容）
    const contentIds = contentList.value.map(item => item.content_id)
    
    const blob = await exportAnalyticsReport({
      content_ids: contentIds,
      format: 'excel'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `content_analytics_${new Date().getTime()}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error('导出报告失败:', error)
    ElMessage.error('导出报告失败')
  }
}

// 组件挂载
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.content-analytics {
  padding: 20px;
}

.summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.stat-item {
  text-align: center;
  padding: 20px 0;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.content-list-card {
  margin-bottom: 20px;
}

.detail-content {
  min-height: 400px;
}

.charts-container {
  margin-top: 20px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>

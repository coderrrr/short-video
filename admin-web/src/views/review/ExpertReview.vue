<template>
  <div class="expert-review-container">
    <!-- 页面标题 -->
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div class="title-section">
          <h2>专家审核管理</h2>
          <p class="subtitle">管理需要专家二审的内容</p>
        </div>
        <div class="stats-section">
          <el-statistic title="待分配" :value="statistics.pending_assign || 0" />
          <el-statistic title="审核中" :value="statistics.in_review || 0" />
          <el-statistic title="已完成" :value="statistics.completed || 0" />
        </div>
      </div>
    </el-card>

    <!-- 筛选和操作栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="审核状态">
          <el-select v-model="filterForm.review_status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="待分配" value="pending_assign" />
            <el-option label="审核中" value="in_review" />
            <el-option label="已批准" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="专家">
          <el-select
            v-model="filterForm.expert_id"
            placeholder="选择专家"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="expert in expertList"
              :key="expert.id"
              :label="expert.name"
              :value="expert.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 内容列表 -->
    <el-card class="content-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="contentList"
        style="width: 100%"
      >
        <el-table-column label="封面" width="120">
          <template #default="{ row }">
            <el-image
              :src="row.cover_url || '/placeholder.png'"
              fit="cover"
              style="width: 100px; height: 60px; border-radius: 4px"
              :preview-src-list="[row.cover_url]"
              :preview-teleported="true"
              :z-index="9999"
            />
          </template>
        </el-table-column>

        <el-table-column label="标题" min-width="200">
          <template #default="{ row }">
            <div class="content-title">
              <el-link type="primary" @click="handleViewDetail(row)">
                {{ row.title }}
              </el-link>
              <el-tag v-if="row.content_type" size="small" style="margin-left: 8px">
                {{ row.content_type }}
              </el-tag>
            </div>
            <div class="content-meta">
              <span>创作者: {{ row.creator?.name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="专家审核状态" width="150">
          <template #default="{ row }">
            <el-tag v-if="!row.expert_review" type="info" size="small">
              待分配
            </el-tag>
            <el-tag v-else-if="row.expert_review.status === 'pending'" type="warning" size="small">
              审核中
            </el-tag>
            <el-tag v-else-if="row.expert_review.status === 'approved'" type="success" size="small">
              已批准
            </el-tag>
            <el-tag v-else-if="row.expert_review.status === 'rejected'" type="danger" size="small">
              已拒绝
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="指定专家" width="150">
          <template #default="{ row }">
            <div v-if="row.expert_review?.expert">
              <el-avatar :size="24" :src="row.expert_review.expert.avatar_url">
                {{ row.expert_review.expert.name?.charAt(0) }}
              </el-avatar>
              <span style="margin-left: 8px">{{ row.expert_review.expert.name }}</span>
            </div>
            <span v-else style="color: #909399">未分配</span>
          </template>
        </el-table-column>

        <el-table-column label="分配时间" width="160">
          <template #default="{ row }">
            {{ row.expert_review?.created_at ? formatDateTime(row.expert_review.created_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="审核时间" width="160">
          <template #default="{ row }">
            {{ row.expert_review?.updated_at ? formatDateTime(row.expert_review.updated_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.expert_review"
              type="primary"
              size="small"
              @click="handleAssignExpert(row)"
            >
              <el-icon><User /></el-icon>
              分配专家
            </el-button>
            <el-button
              v-else
              type="primary"
              size="small"
              @click="handleViewProgress(row)"
            >
              <el-icon><View /></el-icon>
              查看进度
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 分配专家对话框 -->
    <el-dialog
      v-model="assignDialogVisible"
      title="分配专家审核"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="assignForm" :rules="assignRules" ref="assignFormRef" label-width="80px">
        <el-form-item label="内容标题">
          <div>{{ currentContent?.title }}</div>
        </el-form-item>
        
        <el-form-item label="选择专家" prop="expert_id">
          <el-select
            v-model="assignForm.expert_id"
            placeholder="请选择专家"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="expert in expertList"
              :key="expert.id"
              :label="`${expert.name} - ${expert.department}`"
              :value="expert.id"
            >
              <div style="display: flex; align-items: center; gap: 8px">
                <el-avatar :size="24" :src="expert.avatar_url">
                  {{ expert.name?.charAt(0) }}
                </el-avatar>
                <div>
                  <div>{{ expert.name }}</div>
                  <div style="font-size: 12px; color: #909399">{{ expert.department }}</div>
                </div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input
            v-model="assignForm.comment"
            type="textarea"
            :rows="3"
            placeholder="可选：给专家的备注信息"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAssign" :loading="submitting">
          确认分配
        </el-button>
      </template>
    </el-dialog>

    <!-- 审核进度对话框 -->
    <el-dialog
      v-model="progressDialogVisible"
      title="审核进度"
      width="700px"
      :close-on-click-modal="false"
    >
      <div v-if="currentContent" class="progress-content">
        <!-- 内容信息 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题">{{ currentContent.title }}</el-descriptions-item>
          <el-descriptions-item label="内容类型">{{ currentContent.content_type }}</el-descriptions-item>
          <el-descriptions-item label="创作者">{{ currentContent.creator?.name }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ currentContent.creator?.department }}</el-descriptions-item>
        </el-descriptions>

        <!-- 审核时间线 -->
        <div style="margin-top: 20px">
          <h4>审核进度</h4>
          <el-timeline>
            <el-timeline-item
              v-for="record in reviewRecords"
              :key="record.id"
              :timestamp="formatDateTime(record.created_at)"
              :type="getTimelineType(record.status)"
            >
              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="timeline-type">{{ getReviewTypeText(record.review_type) }}</span>
                  <el-tag :type="getStatusTagType(record.status)" size="small">
                    {{ getStatusText(record.status) }}
                  </el-tag>
                </div>
                <div class="timeline-reviewer">
                  审核人: {{ record.reviewer?.name || '系统' }}
                </div>
                <div v-if="record.reason" class="timeline-reason">
                  {{ record.status === 'rejected' ? '拒绝原因' : '备注' }}: {{ record.reason }}
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 视频预览 -->
        <div style="margin-top: 20px">
          <h4>视频预览</h4>
          <video
            v-if="currentContent.video_url"
            :src="currentContent.video_url"
            controls
            style="width: 100%; max-height: 400px"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="progressDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, User, View } from '@element-plus/icons-vue'
import { getContentReviewDetail } from '@/api/review'
import request from '@/api/request'

// 数据
const loading = ref(false)
const contentList = ref([])
const expertList = ref([])
const statistics = ref({})

// 筛选表单
const filterForm = reactive({
  review_status: '',
  expert_id: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 分配专家对话框
const assignDialogVisible = ref(false)
const assignFormRef = ref(null)
const currentContent = ref(null)
const assignForm = reactive({
  expert_id: '',
  comment: ''
})
const assignRules = {
  expert_id: [
    { required: true, message: '请选择专家', trigger: 'change' }
  ]
}
const submitting = ref(false)

// 审核进度对话框
const progressDialogVisible = ref(false)
const reviewRecords = ref([])

// 加载专家列表
const loadExpertList = async () => {
  try {
    // 获取所有KOL用户作为专家
    const response = await request({
      url: '/users/experts',
      method: 'get'
    })
    expertList.value = response.items || []
  } catch (error) {
    console.error('加载专家列表失败:', error)
  }
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...filterForm
    }
    
    // 查询需要专家审核的内容
    const response = await request({
      url: '/admin/contents/expert-review',
      method: 'get',
      params
    })
    
    contentList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await request({
      url: '/admin/contents/expert-review/statistics',
      method: 'get'
    })
    statistics.value = response
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  filterForm.review_status = ''
  filterForm.expert_id = ''
  pagination.page = 1
  loadData()
}

// 分页变化
const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  loadData()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

// 查看详情
const handleViewDetail = (content) => {
  // TODO: 实现详情查看
  ElMessage.info('详情查看功能将在后续版本实现')
}

// 分配专家
const handleAssignExpert = (content) => {
  currentContent.value = content
  assignForm.expert_id = ''
  assignForm.comment = ''
  assignDialogVisible.value = true
}

// 确认分配
const confirmAssign = async () => {
  if (!assignFormRef.value) return
  
  await assignFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      await request({
        url: `/contents/${currentContent.value.id}/expert-review/assign`,
        method: 'post',
        data: {
          expert_id: assignForm.expert_id,
          comment: assignForm.comment
        }
      })
      
      ElMessage.success('分配成功')
      assignDialogVisible.value = false
      loadData()
      loadStatistics()
    } catch (error) {
      console.error('分配失败:', error)
      ElMessage.error('分配失败')
    } finally {
      submitting.value = false
    }
  })
}

// 查看进度
const handleViewProgress = async (content) => {
  currentContent.value = content
  
  try {
    const detail = await getContentReviewDetail(content.id)
    reviewRecords.value = detail.review_records || []
    progressDialogVisible.value = true
  } catch (error) {
    console.error('加载审核记录失败:', error)
    ElMessage.error('加载审核记录失败')
  }
}

// 获取审核类型文本
const getReviewTypeText = (type) => {
  const map = {
    'platform_review': '平台审核',
    'expert_review': '专家审核',
    'ai_review': 'AI审核'
  }
  return map[type] || type
}

// 获取状态文本
const getStatusText = (status) => {
  const map = {
    'pending': '待审核',
    'approved': '已批准',
    'rejected': '已拒绝'
  }
  return map[status] || status
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  const map = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger'
  }
  return map[status] || 'info'
}

// 获取时间线类型
const getTimelineType = (status) => {
  const map = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger'
  }
  return map[status] || 'primary'
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(() => {
  loadExpertList()
  loadData()
  loadStatistics()
})
</script>

<style scoped>
.expert-review-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.stats-section {
  display: flex;
  gap: 40px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
}

.content-card {
  margin-bottom: 20px;
}

.content-title {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.content-meta {
  font-size: 12px;
  color: #909399;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.progress-content {
  max-height: 70vh;
  overflow-y: auto;
}

.timeline-content {
  padding: 8px 0;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.timeline-type {
  font-weight: bold;
  color: #303133;
}

.timeline-reviewer {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.timeline-reason {
  font-size: 13px;
  color: #909399;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-top: 4px;
}
</style>

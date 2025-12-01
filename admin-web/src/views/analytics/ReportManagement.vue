<template>
  <div class="report-management">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">待处理举报</div>
            <div class="stat-value pending">{{ statistics.pending || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">处理中举报</div>
            <div class="stat-value processing">{{ statistics.processing || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">已处理举报</div>
            <div class="stat-value resolved">{{ statistics.resolved || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">总举报数</div>
            <div class="stat-value">{{ statistics.total || 0 }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 举报列表 -->
    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span>举报列表</span>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-select
          v-model="filters.status"
          placeholder="举报状态"
          clearable
          style="width: 150px; margin-right: 10px"
          @change="handleFilter"
        >
          <el-option label="待处理" value="pending" />
          <el-option label="处理中" value="processing" />
          <el-option label="已处理" value="resolved" />
          <el-option label="已驳回" value="rejected" />
        </el-select>
        <el-input
          v-model="filters.content_id"
          placeholder="内容ID"
          clearable
          style="width: 200px; margin-right: 10px"
          @clear="handleFilter"
        />
        <el-button type="primary" @click="handleFilter">筛选</el-button>
        <el-button @click="handleReset">重置</el-button>
      </div>

      <!-- 举报表格 -->
      <el-table
        v-loading="loading"
        :data="reportList"
        style="width: 100%; margin-top: 20px"
        @row-click="handleRowClick"
      >
        <el-table-column prop="report_id" label="举报ID" width="100" show-overflow-tooltip />
        <el-table-column prop="content_title" label="被举报内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reporter_name" label="举报人" width="120" />
        <el-table-column prop="reason" label="举报原因" width="150">
          <template #default="{ row }">
            <el-tag :type="getReasonTagType(row.reason)">
              {{ getReasonText(row.reason) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="举报时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click.stop="viewDetail(row.report_id)"
            >
              查看详情
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              type="success"
              link
              @click.stop="handleProcess(row.report_id)"
            >
              处理
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

    <!-- 举报详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="举报详情"
      width="60%"
      :close-on-click-modal="false"
    >
      <div v-loading="detailLoading" class="detail-content">
        <el-descriptions :column="2" border v-if="detailData">
          <el-descriptions-item label="举报ID">
            {{ detailData.report_id }}
          </el-descriptions-item>
          <el-descriptions-item label="举报状态">
            <el-tag :type="getStatusTagType(detailData.status)">
              {{ getStatusText(detailData.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="举报人">
            {{ detailData.reporter_name }}
          </el-descriptions-item>
          <el-descriptions-item label="举报时间">
            {{ formatDateTime(detailData.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="被举报内容">
            {{ detailData.content_title }}
          </el-descriptions-item>
          <el-descriptions-item label="内容创作者">
            {{ detailData.creator_name }}
          </el-descriptions-item>
          <el-descriptions-item label="举报原因">
            <el-tag :type="getReasonTagType(detailData.reason)">
              {{ getReasonText(detailData.reason) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="处理人" v-if="detailData.handler_name">
            {{ detailData.handler_name }}
          </el-descriptions-item>
          <el-descriptions-item label="详细描述" :span="2">
            {{ detailData.description || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="处理备注" :span="2" v-if="detailData.handler_note">
            {{ detailData.handler_note }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 处理举报对话框 -->
    <el-dialog
      v-model="processDialogVisible"
      title="处理举报"
      width="50%"
      :close-on-click-modal="false"
    >
      <el-form :model="processForm" label-width="100px">
        <el-form-item label="处理结果">
          <el-radio-group v-model="processForm.status">
            <el-radio label="resolved">确认违规</el-radio>
            <el-radio label="rejected">驳回举报</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="处理备注">
          <el-input
            v-model="processForm.handler_note"
            type="textarea"
            :rows="4"
            placeholder="请输入处理备注"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="processDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitProcess" :loading="submitting">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getReportList,
  getReportDetail,
  updateReportStatus,
  getReportStatistics
} from '@/api/report'

// 数据
const loading = ref(false)
const statistics = ref({})
const reportList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选条件
const filters = ref({
  status: '',
  content_id: ''
})

// 详情对话框
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)

// 处理对话框
const processDialogVisible = ref(false)
const submitting = ref(false)
const processForm = ref({
  report_id: '',
  status: 'resolved',
  handler_note: ''
})

// 加载统计数据
const loadStatistics = async () => {
  try {
    const response = await getReportStatistics()
    statistics.value = response
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载举报列表
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      status: filters.value.status || undefined,
      content_id: filters.value.content_id || undefined
    }

    const response = await getReportList(params)
    reportList.value = response.reports || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载举报列表失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 获取状态标签类型
const getStatusTagType = (status) => {
  const typeMap = {
    pending: 'warning',
    processing: 'info',
    resolved: 'success',
    rejected: 'danger'
  }
  return typeMap[status] || ''
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    pending: '待处理',
    processing: '处理中',
    resolved: '已处理',
    rejected: '已驳回'
  }
  return textMap[status] || status
}

// 获取原因标签类型
const getReasonTagType = (reason) => {
  const typeMap = {
    inappropriate: 'danger',
    spam: 'warning',
    misleading: 'warning',
    copyright: 'info',
    other: ''
  }
  return typeMap[reason] || ''
}

// 获取原因文本
const getReasonText = (reason) => {
  const textMap = {
    inappropriate: '不当内容',
    spam: '垃圾信息',
    misleading: '误导信息',
    copyright: '版权问题',
    other: '其他'
  }
  return textMap[reason] || reason
}

// 筛选
const handleFilter = () => {
  currentPage.value = 1
  loadData()
}

// 重置
const handleReset = () => {
  filters.value = {
    status: '',
    content_id: ''
  }
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
  viewDetail(row.report_id)
}

// 查看详情
const viewDetail = async (reportId) => {
  detailDialogVisible.value = true
  detailLoading.value = true
  
  try {
    const response = await getReportDetail(reportId)
    detailData.value = response
  } catch (error) {
    console.error('加载举报详情失败:', error)
    ElMessage.error('加载详情失败')
  } finally {
    detailLoading.value = false
  }
}

// 处理举报
const handleProcess = (reportId) => {
  processForm.value = {
    report_id: reportId,
    status: 'resolved',
    handler_note: ''
  }
  processDialogVisible.value = true
}

// 提交处理
const submitProcess = async () => {
  if (!processForm.value.handler_note.trim()) {
    ElMessage.warning('请输入处理备注')
    return
  }

  submitting.value = true
  try {
    await updateReportStatus(processForm.value.report_id, {
      status: processForm.value.status,
      handler_note: processForm.value.handler_note
    })
    
    ElMessage.success('处理成功')
    processDialogVisible.value = false
    loadData()
    loadStatistics()
  } catch (error) {
    console.error('处理举报失败:', error)
    ElMessage.error('处理失败')
  } finally {
    submitting.value = false
  }
}

// 组件挂载
onMounted(() => {
  loadStatistics()
  loadData()
})
</script>

<style scoped>
.report-management {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
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

.stat-value.pending {
  color: #E6A23C;
}

.stat-value.processing {
  color: #409EFF;
}

.stat-value.resolved {
  color: #67C23A;
}

.list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.detail-content {
  min-height: 200px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>

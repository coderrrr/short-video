<template>
  <div class="kol-management">
    <!-- 页面标题和操作栏 -->
    <div class="header">
      <h2>KOL管理</h2>
      <div class="actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建KOL账号
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索姓名或员工ID"
        clearable
        @clear="loadKOLs"
        @keyup.enter="loadKOLs"
        style="width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="loadKOLs" style="margin-left: 10px">
        搜索
      </el-button>
    </div>

    <!-- KOL表格 -->
    <el-table
      :data="kols"
      v-loading="loading"
      style="width: 100%; margin-top: 20px"
    >
      <el-table-column label="头像" width="80">
        <template #default="{ row }">
          <el-avatar :src="row.avatar_url" :size="50">
            {{ row.name.charAt(0) }}
          </el-avatar>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="employee_id" label="员工ID" width="120" />
      <el-table-column prop="department" label="部门" width="150" />
      <el-table-column prop="position" label="职位" width="150" />
      <el-table-column prop="content_count" label="发布内容数" width="120" align="center" />
      <el-table-column prop="follower_count" label="粉丝数" width="100" align="center" />
      <el-table-column label="KOL状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.is_kol" type="success">已授权</el-tag>
          <el-tag v-else type="info">未授权</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="授权时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="handleViewDetail(row)">
            查看详情
          </el-button>
          <el-button link type="danger" size="small" @click="handleRevoke(row)">
            撤销
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadKOLs"
        @current-change="loadKOLs"
      />
    </div>

    <!-- 创建KOL对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建KOL账号"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="选择用户" prop="user_id">
          <el-select
            v-model="formData.user_id"
            placeholder="请搜索并选择用户"
            filterable
            remote
            :remote-method="searchUserRemote"
            :loading="userSearchLoading"
            style="width: 100%"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="`${user.name} (${user.employee_id}) - ${user.department}`"
              :value="user.id"
            >
              <div style="display: flex; align-items: center">
                <el-avatar :src="user.avatar_url" :size="30" style="margin-right: 10px">
                  {{ user.name.charAt(0) }}
                </el-avatar>
                <div>
                  <div>{{ user.name }} ({{ user.employee_id }})</div>
                  <div style="font-size: 12px; color: #999">
                    {{ user.department }} - {{ user.position }}
                  </div>
                </div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-alert
          title="授权说明"
          type="info"
          :closable="false"
          style="margin-top: 10px"
        >
          <p>授权为KOL后，该用户将获得以下权限：</p>
          <ul>
            <li>后台内容上传权限</li>
            <li>个人资料显示KOL徽章</li>
            <li>内容优先推荐</li>
          </ul>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- KOL详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="KOL详情"
      width="700px"
    >
      <div v-if="currentKOL" class="kol-detail">
        <div class="detail-header">
          <el-avatar :src="currentKOL.avatar_url" :size="80">
            {{ currentKOL.name.charAt(0) }}
          </el-avatar>
          <div class="detail-info">
            <h3>{{ currentKOL.name }}</h3>
            <p>员工ID: {{ currentKOL.employee_id }}</p>
            <p>{{ currentKOL.department }} - {{ currentKOL.position }}</p>
          </div>
        </div>
        <el-divider />
        <div class="detail-stats">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="发布内容数" :value="currentKOL.content_count" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="粉丝数" :value="currentKOL.follower_count" />
            </el-col>
            <el-col :span="8">
              <div class="statistic">
                <div class="statistic-title">KOL状态</div>
                <el-tag v-if="currentKOL.is_kol" type="success" size="large">已授权</el-tag>
              </div>
            </el-col>
          </el-row>
        </div>
        <el-divider />
        <div class="detail-time">
          <p><strong>授权时间：</strong>{{ formatDate(currentKOL.created_at) }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getKOLList,
  getKOLDetail,
  createKOL,
  revokeKOL,
  searchUsers
} from '@/api/kol'

// 数据状态
const loading = ref(false)
const kols = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')

// 对话框状态
const dialogVisible = ref(false)
const formRef = ref(null)
const submitting = ref(false)

// 用户搜索
const userSearchLoading = ref(false)
const userOptions = ref([])

// 详情对话框
const detailDialogVisible = ref(false)
const currentKOL = ref(null)

// 表单数据
const formData = reactive({
  user_id: ''
})

// 表单验证规则
const formRules = {
  user_id: [
    { required: true, message: '请选择用户', trigger: 'change' }
  ]
}

// 加载KOL列表
const loadKOLs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }

    const response = await getKOLList(params)
    kols.value = response.kols || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载KOL列表失败:', error)
    ElMessage.error('加载KOL列表失败')
  } finally {
    loading.value = false
  }
}

// 远程搜索用户
const searchUserRemote = async (query) => {
  if (!query) {
    userOptions.value = []
    return
  }

  userSearchLoading.value = true
  try {
    const response = await searchUsers({ search: query })
    userOptions.value = response.items || []
  } catch (error) {
    console.error('搜索用户失败:', error)
    ElMessage.error('搜索用户失败')
  } finally {
    userSearchLoading.value = false
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 创建KOL
const handleCreate = () => {
  dialogVisible.value = true
}

// 查看详情
const handleViewDetail = async (row) => {
  try {
    const response = await getKOLDetail(row.id)
    currentKOL.value = response
    detailDialogVisible.value = true
  } catch (error) {
    console.error('获取KOL详情失败:', error)
    ElMessage.error('获取KOL详情失败')
  }
}

// 撤销KOL
const handleRevoke = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要撤销 ${row.name} 的KOL状态吗？撤销后该用户将失去后台上传权限和KOL徽章。`,
      '确认撤销',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  try {
    await revokeKOL(row.id)
    ElMessage.success('撤销成功')
    loadKOLs()
  } catch (error) {
    console.error('撤销KOL失败:', error)
    ElMessage.error(error.response?.data?.detail || '撤销失败')
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const data = {
      user_id: formData.user_id
    }

    await createKOL(data)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    loadKOLs()
  } catch (error) {
    console.error('创建KOL失败:', error)
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  formData.user_id = ''
  userOptions.value = []
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 页面加载时获取KOL列表
onMounted(() => {
  loadKOLs()
})
</script>

<style scoped>
.kol-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.search-bar {
  display: flex;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.kol-detail {
  padding: 10px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.detail-info h3 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.detail-info p {
  margin: 5px 0;
  color: #666;
}

.detail-stats {
  margin: 20px 0;
}

.statistic {
  text-align: center;
}

.statistic-title {
  font-size: 14px;
  color: #999;
  margin-bottom: 10px;
}

.detail-time p {
  margin: 5px 0;
  color: #666;
}
</style>

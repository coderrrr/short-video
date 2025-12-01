<template>
  <div class="user-list">
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="姓名或员工ID"
            clearable
            @clear="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="用户类型">
          <el-select v-model="filterForm.is_kol" placeholder="全部" clearable @change="handleSearch">
            <el-option label="全部用户" :value="null" />
            <el-option label="普通用户" :value="false" />
            <el-option label="KOL用户" :value="true" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleCreate">新建用户</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="userList"
        style="width: 100%"
        stripe
      >
        <el-table-column prop="employee_id" label="员工ID" width="120" />
        
        <el-table-column label="用户信息" width="250">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :size="40" :src="row.avatar_url">
                {{ row.name?.charAt(0) }}
              </el-avatar>
              <div class="user-details">
                <div class="user-name">{{ row.name }}</div>
                <div class="user-meta">{{ row.department }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="position" label="职位" width="150" />
        
        <el-table-column label="用户类型" width="150">
          <template #default="{ row }">
            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
              <el-tag v-if="row.is_admin" type="danger" size="small">
                管理员
              </el-tag>
              <el-tag :type="row.is_kol ? 'success' : 'info'" size="small">
                {{ row.is_kol ? 'KOL' : '普通用户' }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="统计数据" width="200">
          <template #default="{ row }">
            <div class="stats">
              <span>关注: {{ row.following_count || 0 }}</span>
              <span>粉丝: {{ row.followers_count || 0 }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleView(row)"
            >
              查看
            </el-button>
            <el-button
              type="warning"
              size="small"
              link
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              :type="row.is_kol ? 'warning' : 'success'"
              size="small"
              link
              @click="handleToggleKol(row)"
            >
              {{ row.is_kol ? '取消KOL' : '设为KOL' }}
            </el-button>
            <el-button
              :type="row.is_admin ? 'warning' : 'danger'"
              size="small"
              link
              @click="handleToggleAdmin(row)"
            >
              {{ row.is_admin ? '取消管理员' : '设为管理员' }}
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        class="pagination"
      />
    </el-card>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建用户"
      width="500px"
      @close="handleCreateDialogClose"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="员工ID" prop="employee_id">
          <el-input v-model="createForm.employee_id" placeholder="请输入员工ID" />
        </el-form-item>
        
        <el-form-item label="姓名" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入姓名" />
        </el-form-item>
        
        <el-form-item label="部门" prop="department">
          <el-input v-model="createForm.department" placeholder="请输入部门" />
        </el-form-item>
        
        <el-form-item label="职位" prop="position">
          <el-input v-model="createForm.position" placeholder="请输入职位" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreateSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑用户"
      width="500px"
      @close="handleEditDialogClose"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="员工ID">
          <el-input v-model="editForm.employee_id" disabled />
        </el-form-item>
        
        <el-form-item label="姓名" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入姓名" />
        </el-form-item>
        
        <el-form-item label="部门" prop="department">
          <el-input v-model="editForm.department" placeholder="请输入部门" />
        </el-form-item>
        
        <el-form-item label="职位" prop="position">
          <el-input v-model="editForm.position" placeholder="请输入职位" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleEditSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 用户详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="用户详情"
      width="700px"
    >
      <div v-if="currentUser" class="user-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="员工ID">
            {{ currentUser.employee_id }}
          </el-descriptions-item>
          <el-descriptions-item label="姓名">
            {{ currentUser.name }}
          </el-descriptions-item>
          <el-descriptions-item label="部门">
            {{ currentUser.department }}
          </el-descriptions-item>
          <el-descriptions-item label="职位">
            {{ currentUser.position }}
          </el-descriptions-item>
          <el-descriptions-item label="用户类型">
            <div style="display: flex; gap: 8px;">
              <el-tag v-if="currentUser.is_admin" type="danger">
                管理员
              </el-tag>
              <el-tag :type="currentUser.is_kol ? 'success' : 'info'">
                {{ currentUser.is_kol ? 'KOL' : '普通用户' }}
              </el-tag>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(currentUser.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider>统计数据</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="关注数" :value="userStats.following_count || 0" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="粉丝数" :value="userStats.followers_count || 0" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="发布内容" :value="userStats.content_count || 0" />
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getUserList, searchUsers, createUser, updateUser, deleteUser, updateUserKolStatus, updateUserAdminStatus, getUserFollowCounts, getCreatorProfile } from '../../api/user'

// 筛选表单
const filterForm = reactive({
  search: '',
  is_kol: null
})

// 用户列表
const userList = ref([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 创建用户对话框
const createDialogVisible = ref(false)
const createFormRef = ref(null)
const createLoading = ref(false)
const createForm = reactive({
  employee_id: '',
  name: '',
  department: '',
  position: '',
  password: ''
})

const createRules = {
  employee_id: [
    { required: true, message: '请输入员工ID', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  department: [
    { required: true, message: '请输入部门', trigger: 'blur' }
  ],
  position: [
    { required: true, message: '请输入职位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

// 编辑用户对话框
const editDialogVisible = ref(false)
const editFormRef = ref(null)
const editLoading = ref(false)
const editForm = reactive({
  id: '',
  employee_id: '',
  name: '',
  department: '',
  position: ''
})

const editRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  department: [
    { required: true, message: '请输入部门', trigger: 'blur' }
  ],
  position: [
    { required: true, message: '请输入职位', trigger: 'blur' }
  ]
}

// 用户详情对话框
const detailDialogVisible = ref(false)
const currentUser = ref(null)
const userStats = ref({})

// 加载用户列表
const loadUserList = async (skipCache = false) => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    }
    
    // 如果需要跳过缓存，添加时间戳
    if (skipCache) {
      params._t = Date.now()
    }
    
    let response
    if (filterForm.search) {
      // 使用搜索接口
      response = await searchUsers({
        ...params,
        search: filterForm.search
      })
      userList.value = response.items || []
      pagination.total = response.total || 0
    } else {
      // 使用列表接口
      if (filterForm.is_kol !== null) {
        params.is_kol = filterForm.is_kol
      }
      const data = await getUserList(params)
      userList.value = Array.isArray(data) ? data : []
      pagination.total = userList.value.length
    }
    
    // 加载每个用户的统计数据
    await loadUserStats()
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 加载用户统计数据
const loadUserStats = async () => {
  for (const user of userList.value) {
    try {
      const stats = await getUserFollowCounts(user.id)
      user.following_count = stats.following_count
      user.followers_count = stats.followers_count
    } catch (error) {
      console.error(`加载用户 ${user.id} 统计数据失败:`, error)
    }
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadUserList()
}

// 重置
const handleReset = () => {
  filterForm.search = ''
  filterForm.is_kol = null
  pagination.page = 1
  loadUserList()
}

// 新建用户
const handleCreate = () => {
  createDialogVisible.value = true
}

// 创建用户对话框关闭
const handleCreateDialogClose = () => {
  createFormRef.value?.resetFields()
  Object.assign(createForm, {
    employee_id: '',
    name: '',
    department: '',
    position: '',
    password: ''
  })
}

// 提交创建用户
const handleCreateSubmit = async () => {
  try {
    await createFormRef.value.validate()
    createLoading.value = true
    
    await createUser(createForm)
    
    // 先刷新列表（跳过缓存）
    await loadUserList(true)
    
    // 再关闭对话框和显示成功消息
    createDialogVisible.value = false
    ElMessage.success('创建用户成功')
  } catch (error) {
    if (error !== false) {
      console.error('创建用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '创建用户失败')
    }
  } finally {
    createLoading.value = false
  }
}

// 编辑用户
const handleEdit = (user) => {
  Object.assign(editForm, {
    id: user.id,
    employee_id: user.employee_id,
    name: user.name,
    department: user.department,
    position: user.position
  })
  editDialogVisible.value = true
}

// 编辑用户对话框关闭
const handleEditDialogClose = () => {
  editFormRef.value?.resetFields()
  Object.assign(editForm, {
    id: '',
    employee_id: '',
    name: '',
    department: '',
    position: ''
  })
}

// 提交编辑用户
const handleEditSubmit = async () => {
  try {
    await editFormRef.value.validate()
    editLoading.value = true
    
    await updateUser(editForm.id, {
      name: editForm.name,
      department: editForm.department,
      position: editForm.position
    })
    
    // 先刷新列表
    await loadUserList(true)
    
    // 再关闭对话框和显示成功消息
    editDialogVisible.value = false
    ElMessage.success('更新用户成功')
  } catch (error) {
    if (error !== false) {
      console.error('更新用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '更新用户失败')
    }
  } finally {
    editLoading.value = false
  }
}

// 删除用户
const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${user.name} (${user.employee_id}) 吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    await deleteUser(user.id)
    
    ElMessage.success('删除用户成功')
    await loadUserList(true)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除用户失败')
    }
  }
}

// 查看用户详情
const handleView = async (user) => {
  try {
    currentUser.value = user
    
    // 加载详细统计数据
    const profile = await getCreatorProfile(user.id)
    userStats.value = {
      following_count: profile.following_count,
      followers_count: profile.followers_count,
      content_count: profile.content_count
    }
    
    detailDialogVisible.value = true
  } catch (error) {
    console.error('加载用户详情失败:', error)
    ElMessage.error('加载用户详情失败')
  }
}

// 切换KOL状态
const handleToggleKol = async (user) => {
  try {
    const action = user.is_kol ? '取消KOL' : '设为KOL'
    await ElMessageBox.confirm(
      `确定要${action}用户 ${user.name} 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await updateUserKolStatus(user.id, { is_kol: !user.is_kol })
    
    ElMessage.success(`${action}成功`)
    await loadUserList(true)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('更新KOL状态失败:', error)
      ElMessage.error('更新KOL状态失败')
    }
  }
}

// 切换管理员状态
const handleToggleAdmin = async (user) => {
  try {
    const action = user.is_admin ? '取消管理员' : '设为管理员'
    await ElMessageBox.confirm(
      `确定要${action}用户 ${user.name} 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await updateUserAdminStatus(user.id, { is_admin: !user.is_admin })
    
    ElMessage.success(`${action}成功`)
    await loadUserList(true)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('更新管理员状态失败:', error)
      ElMessage.error('更新管理员状态失败')
    }
  }
}

// 分页大小改变
const handleSizeChange = () => {
  pagination.page = 1
  loadUserList()
}

// 页码改变
const handlePageChange = () => {
  loadUserList()
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

onMounted(() => {
  loadUserList()
})
</script>

<style scoped>
.user-list {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
}

.table-card {
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-details {
  flex: 1;
}

.user-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.user-meta {
  font-size: 12px;
  color: #909399;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.user-detail {
  padding: 20px 0;
}

.user-detail .el-divider {
  margin: 30px 0 20px;
}
</style>

<template>
  <div class="tag-management">
    <!-- 页面标题和操作栏 -->
    <div class="header">
      <h2>标签管理</h2>
      <div class="actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建标签
        </el-button>
      </div>
    </div>

    <!-- 筛选和搜索栏 -->
    <div class="filter-bar">
      <el-select
        v-model="filterCategory"
        placeholder="标签分类"
        clearable
        @change="loadTags"
        style="width: 200px"
      >
        <el-option label="角色标签" value="角色标签" />
        <el-option label="主题标签" value="主题标签" />
        <el-option label="形式标签" value="形式标签" />
        <el-option label="质量标签" value="质量标签" />
        <el-option label="推荐标签" value="推荐标签" />
      </el-select>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索标签名称"
        clearable
        @clear="loadTags"
        @keyup.enter="loadTags"
        style="width: 300px; margin-left: 10px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="loadTags" style="margin-left: 10px">
        搜索
      </el-button>
      <el-button @click="handleBatchAssign" style="margin-left: 10px" :disabled="selectedTags.length === 0">
        批量分配
      </el-button>
    </div>

    <!-- 标签表格 -->
    <el-table
      :data="tags"
      v-loading="loading"
      @selection-change="handleSelectionChange"
      style="width: 100%; margin-top: 20px"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="name" label="标签名称" min-width="150" />
      <el-table-column prop="category" label="标签分类" width="120" />
      <el-table-column prop="parent_id" label="父标签" width="150">
        <template #default="{ row }">
          {{ row.parent_id ? getParentTagName(row.parent_id) : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="children_count" label="子标签数" width="100" align="center" />
      <el-table-column prop="content_count" label="内容数" width="100" align="center" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row)">
            删除
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
        @size-change="loadTags"
        @current-change="loadTags"
      />
    </div>

    <!-- 创建/编辑标签对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="标签名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="标签分类" prop="category">
          <el-select v-model="formData.category" placeholder="请选择标签分类">
            <el-option label="角色标签" value="角色标签" />
            <el-option label="主题标签" value="主题标签" />
            <el-option label="形式标签" value="形式标签" />
            <el-option label="质量标签" value="质量标签" />
            <el-option label="推荐标签" value="推荐标签" />
          </el-select>
        </el-form-item>
        <el-form-item label="父标签" prop="parent_id">
          <el-select
            v-model="formData.parent_id"
            placeholder="请选择父标签（可选）"
            clearable
            filterable
          >
            <el-option
              v-for="tag in parentTagOptions"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量分配标签对话框 -->
    <el-dialog
      v-model="batchDialogVisible"
      title="批量分配标签"
      width="600px"
    >
      <el-form label-width="100px">
        <el-form-item label="选中标签">
          <el-tag
            v-for="tag in selectedTags"
            :key="tag.id"
            style="margin-right: 10px"
          >
            {{ tag.name }}
          </el-tag>
        </el-form-item>
        <el-form-item label="目标内容">
          <el-input
            v-model="batchContentIds"
            type="textarea"
            :rows="4"
            placeholder="请输入内容ID，多个ID用逗号或换行分隔"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchSubmit" :loading="batchSubmitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getTagList,
  createTag,
  updateTag,
  deleteTag,
  batchAssignTags
} from '@/api/tag'

// 数据状态
const loading = ref(false)
const tags = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterCategory = ref('')
const searchKeyword = ref('')
const selectedTags = ref([])

// 对话框状态
const dialogVisible = ref(false)
const dialogTitle = ref('创建标签')
const formRef = ref(null)
const submitting = ref(false)
const editingId = ref(null)

// 批量分配对话框
const batchDialogVisible = ref(false)
const batchContentIds = ref('')
const batchSubmitting = ref(false)

// 表单数据
const formData = reactive({
  name: '',
  category: '',
  parent_id: null
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入标签名称', trigger: 'blur' },
    { min: 1, max: 50, message: '标签名称长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择标签分类', trigger: 'change' }
  ]
}

// 父标签选项（排除当前编辑的标签）
const parentTagOptions = computed(() => {
  return tags.value.filter(tag => tag.id !== editingId.value)
})

// 加载标签列表
const loadTags = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterCategory.value) {
      params.category = filterCategory.value
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }

    const response = await getTagList(params)
    tags.value = response.tags || []
    total.value = response.total || 0
  } catch (error) {
    console.error('加载标签失败:', error)
    ElMessage.error('加载标签失败')
  } finally {
    loading.value = false
  }
}

// 获取父标签名称
const getParentTagName = (parentId) => {
  const parent = tags.value.find(tag => tag.id === parentId)
  return parent ? parent.name : '-'
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

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedTags.value = selection
}

// 创建标签
const handleCreate = () => {
  dialogTitle.value = '创建标签'
  editingId.value = null
  dialogVisible.value = true
}

// 编辑标签
const handleEdit = (row) => {
  dialogTitle.value = '编辑标签'
  editingId.value = row.id
  formData.name = row.name
  formData.category = row.category
  formData.parent_id = row.parent_id || null
  dialogVisible.value = true
}

// 删除标签
const handleDelete = async (row) => {
  // 检查是否有子标签
  if (row.children_count > 0) {
    try {
      await ElMessageBox.confirm(
        `该标签下有 ${row.children_count} 个子标签，是否强制删除（包括所有子标签和内容关联）？`,
        '确认删除',
        {
          confirmButtonText: '强制删除',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      // 强制删除
      await deleteTag(row.id, { force: true })
      ElMessage.success('删除成功')
      loadTags()
      return
    } catch {
      return
    }
  }

  // 检查是否有关联内容
  if (row.content_count > 0) {
    try {
      await ElMessageBox.confirm(
        `该标签下有 ${row.content_count} 个内容，删除后这些内容将失去该标签。确定要删除吗？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  } else {
    try {
      await ElMessageBox.confirm(
        '确定要删除该标签吗？',
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }

  try {
    await deleteTag(row.id)
    ElMessage.success('删除成功')
    loadTags()
  } catch (error) {
    console.error('删除标签失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

// 批量分配
const handleBatchAssign = () => {
  batchContentIds.value = ''
  batchDialogVisible.value = true
}

// 提交批量分配
const handleBatchSubmit = async () => {
  if (!batchContentIds.value.trim()) {
    ElMessage.warning('请输入内容ID')
    return
  }

  // 解析内容ID
  const contentIds = batchContentIds.value
    .split(/[,\n]/)
    .map(id => id.trim())
    .filter(id => id)

  if (contentIds.length === 0) {
    ElMessage.warning('请输入有效的内容ID')
    return
  }

  batchSubmitting.value = true
  try {
    const data = {
      content_ids: contentIds,
      tag_ids: selectedTags.value.map(tag => tag.id)
    }

    const response = await batchAssignTags(data)
    ElMessage.success(`成功分配 ${response.success_count} 个内容`)
    batchDialogVisible.value = false
  } catch (error) {
    console.error('批量分配失败:', error)
    ElMessage.error(error.response?.data?.detail || '批量分配失败')
  } finally {
    batchSubmitting.value = false
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
      name: formData.name,
      category: formData.category,
      parent_id: formData.parent_id || null
    }

    if (editingId.value) {
      // 更新标签
      await updateTag(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      // 创建标签
      await createTag(data)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    loadTags()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  formData.name = ''
  formData.category = ''
  formData.parent_id = null
  editingId.value = null
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 页面加载时获取标签列表
onMounted(() => {
  loadTags()
})
</script>

<style scoped>
.tag-management {
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

.filter-bar {
  display: flex;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

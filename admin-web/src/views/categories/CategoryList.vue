<template>
  <div class="category-management">
    <!-- 页面标题和操作栏 -->
    <div class="header">
      <h2>分类管理</h2>
      <div class="actions">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建分类
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索分类名称"
        clearable
        @clear="loadCategories"
        @keyup.enter="loadCategories"
        style="width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="loadCategories" style="margin-left: 10px">
        搜索
      </el-button>
    </div>

    <!-- 分类树形表格 -->
    <el-table
      :data="categoryTree"
      row-key="id"
      :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
      v-loading="loading"
      style="width: 100%; margin-top: 20px"
    >
      <el-table-column prop="name" label="分类名称" min-width="200" />
      <el-table-column prop="children_count" label="子分类数" width="120" align="center" />
      <el-table-column prop="content_count" label="内容数" width="120" align="center" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="handleCreateChild(row)">
            添加子分类
          </el-button>
          <el-button link type="primary" size="small" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑分类对话框 -->
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
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="父分类" prop="parent_id">
          <el-tree-select
            v-model="formData.parent_id"
            :data="categoryTreeOptions"
            :props="{ label: 'name', value: 'id' }"
            placeholder="请选择父分类（可选）"
            clearable
            check-strictly
            :render-after-expand="false"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
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
  getCategoryTree,
  createCategory,
  updateCategory,
  deleteCategory
} from '@/api/category'

// 数据状态
const loading = ref(false)
const categoryTree = ref([])
const searchKeyword = ref('')

// 对话框状态
const dialogVisible = ref(false)
const dialogTitle = ref('创建分类')
const formRef = ref(null)
const submitting = ref(false)
const editingId = ref(null)

// 表单数据
const formData = reactive({
  name: '',
  parent_id: null
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 1, max: 50, message: '分类名称长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

// 用于树形选择器的分类选项（排除当前编辑的分类及其子分类）
const categoryTreeOptions = computed(() => {
  if (!editingId.value) {
    return categoryTree.value
  }
  // 递归过滤掉当前编辑的分类及其子分类
  const filterCategory = (categories) => {
    return categories
      .filter(cat => cat.id !== editingId.value)
      .map(cat => ({
        ...cat,
        children: cat.children ? filterCategory(cat.children) : []
      }))
  }
  return filterCategory(categoryTree.value)
})

// 加载分类树
const loadCategories = async () => {
  loading.value = true
  try {
    const response = await getCategoryTree()
    categoryTree.value = response || []
  } catch (error) {
    console.error('加载分类失败:', error)
    ElMessage.error('加载分类失败')
  } finally {
    loading.value = false
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

// 创建分类
const handleCreate = () => {
  dialogTitle.value = '创建分类'
  editingId.value = null
  dialogVisible.value = true
}

// 创建子分类
const handleCreateChild = (row) => {
  dialogTitle.value = '创建子分类'
  editingId.value = null
  formData.parent_id = row.id
  dialogVisible.value = true
}

// 编辑分类
const handleEdit = (row) => {
  dialogTitle.value = '编辑分类'
  editingId.value = row.id
  formData.name = row.name
  formData.parent_id = row.parent_id || null
  dialogVisible.value = true
}

// 删除分类
const handleDelete = async (row) => {
  // 检查是否有子分类
  if (row.children_count > 0) {
    ElMessage.warning('该分类下有子分类，无法删除')
    return
  }

  // 检查是否有关联内容
  if (row.content_count > 0) {
    try {
      await ElMessageBox.confirm(
        `该分类下有 ${row.content_count} 个内容，删除后这些内容将失去该分类标记。确定要删除吗？`,
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
        '确定要删除该分类吗？',
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
    await deleteCategory(row.id)
    ElMessage.success('删除成功')
    // 立即刷新列表
    await loadCategories()
  } catch (error) {
    console.error('删除分类失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除失败')
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
      parent_id: formData.parent_id || null
    }

    if (editingId.value) {
      // 更新分类
      await updateCategory(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      // 创建分类
      await createCategory(data)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    // 立即刷新列表
    await loadCategories()
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
  formData.parent_id = null
  editingId.value = null
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 页面加载时获取分类列表
onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.category-management {
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
</style>

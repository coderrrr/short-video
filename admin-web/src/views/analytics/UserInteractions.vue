<template>
  <div class="user-interactions">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>用户互动管理</span>
        </div>
      </template>

      <!-- 互动类型选项卡 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="收藏记录" name="favorites">
          <div class="filter-bar">
            <el-input
              v-model="filters.user_id"
              placeholder="用户ID"
              clearable
              style="width: 200px; margin-right: 10px"
              @clear="handleFilter"
            />
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

          <el-table
            v-loading="loading"
            :data="favoriteList"
            style="width: 100%; margin-top: 20px"
          >
            <el-table-column prop="user_name" label="用户" width="120" />
            <el-table-column prop="user_department" label="部门" width="150" />
            <el-table-column prop="content_title" label="内容标题" min-width="200" />
            <el-table-column prop="creator_name" label="创作者" width="120" />
            <el-table-column prop="created_at" label="收藏时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
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
        </el-tab-pane>

        <el-tab-pane label="点赞记录" name="likes">
          <div class="filter-bar">
            <el-input
              v-model="filters.user_id"
              placeholder="用户ID"
              clearable
              style="width: 200px; margin-right: 10px"
              @clear="handleFilter"
            />
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

          <el-table
            v-loading="loading"
            :data="likeList"
            style="width: 100%; margin-top: 20px"
          >
            <el-table-column prop="user_name" label="用户" width="120" />
            <el-table-column prop="user_department" label="部门" width="150" />
            <el-table-column prop="content_title" label="内容标题" min-width="200" />
            <el-table-column prop="creator_name" label="创作者" width="120" />
            <el-table-column prop="created_at" label="点赞时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
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
        </el-tab-pane>

        <el-tab-pane label="标记记录" name="bookmarks">
          <div class="filter-bar">
            <el-input
              v-model="filters.user_id"
              placeholder="用户ID"
              clearable
              style="width: 200px; margin-right: 10px"
              @clear="handleFilter"
            />
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

          <el-table
            v-loading="loading"
            :data="bookmarkList"
            style="width: 100%; margin-top: 20px"
          >
            <el-table-column prop="user_name" label="用户" width="120" />
            <el-table-column prop="user_department" label="部门" width="150" />
            <el-table-column prop="content_title" label="内容标题" min-width="200" />
            <el-table-column prop="creator_name" label="创作者" width="120" />
            <el-table-column prop="note" label="笔记" min-width="200" show-overflow-tooltip />
            <el-table-column prop="created_at" label="标记时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
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
        </el-tab-pane>

        <el-tab-pane label="评论管理" name="comments">
          <div class="filter-bar">
            <el-input
              v-model="filters.user_id"
              placeholder="用户ID"
              clearable
              style="width: 200px; margin-right: 10px"
              @clear="handleFilter"
            />
            <el-input
              v-model="filters.content_id"
              placeholder="内容ID"
              clearable
              style="width: 200px; margin-right: 10px"
              @clear="handleFilter"
            />
            <el-input
              v-model="filters.search_text"
              placeholder="搜索评论内容"
              clearable
              style="width: 200px; margin-right: 10px"
              @clear="handleFilter"
            />
            <el-button type="primary" @click="handleFilter">筛选</el-button>
            <el-button @click="handleReset">重置</el-button>
          </div>

          <el-table
            v-loading="loading"
            :data="commentList"
            style="width: 100%; margin-top: 20px"
          >
            <el-table-column prop="user_name" label="用户" width="120" />
            <el-table-column prop="user_department" label="部门" width="150" />
            <el-table-column prop="content_title" label="内容标题" min-width="180" />
            <el-table-column prop="text" label="评论内容" min-width="250" show-overflow-tooltip />
            <el-table-column prop="created_at" label="评论时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-popconfirm
                  title="确定要删除这条评论吗？"
                  @confirm="handleDeleteComment(row.comment_id)"
                >
                  <template #reference>
                    <el-button type="danger" link>删除</el-button>
                  </template>
                </el-popconfirm>
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
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getFavoriteRecords,
  getLikeRecords,
  getBookmarkRecords,
  getCommentRecords,
  deleteComment
} from '@/api/analytics'

// 数据
const loading = ref(false)
const activeTab = ref('favorites')
const favoriteList = ref([])
const likeList = ref([])
const bookmarkList = ref([])
const commentList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选条件
const filters = ref({
  user_id: '',
  content_id: '',
  search_text: ''
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      user_id: filters.value.user_id || undefined,
      content_id: filters.value.content_id || undefined
    }

    let response
    switch (activeTab.value) {
      case 'favorites':
        response = await getFavoriteRecords(params)
        favoriteList.value = response.records || []
        break
      case 'likes':
        response = await getLikeRecords(params)
        likeList.value = response.records || []
        break
      case 'bookmarks':
        response = await getBookmarkRecords(params)
        bookmarkList.value = response.records || []
        break
      case 'comments':
        params.search_text = filters.value.search_text || undefined
        response = await getCommentRecords(params)
        commentList.value = response.comments || []
        break
    }
    
    total.value = response.total || 0
  } catch (error) {
    console.error('加载互动数据失败:', error)
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

// 选项卡切换
const handleTabChange = () => {
  currentPage.value = 1
  filters.value = {
    user_id: '',
    content_id: '',
    search_text: ''
  }
  loadData()
}

// 筛选
const handleFilter = () => {
  currentPage.value = 1
  loadData()
}

// 重置
const handleReset = () => {
  filters.value = {
    user_id: '',
    content_id: '',
    search_text: ''
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

// 删除评论
const handleDeleteComment = async (commentId) => {
  try {
    await deleteComment(commentId)
    ElMessage.success('评论已删除')
    loadData()
  } catch (error) {
    console.error('删除评论失败:', error)
    ElMessage.error('删除评论失败')
  }
}

// 组件挂载
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.user-interactions {
  padding: 20px;
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
</style>

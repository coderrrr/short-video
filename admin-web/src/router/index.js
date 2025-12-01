import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', noAuth: true }
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表板' }
      },
      {
        path: 'content',
        name: 'ContentManagement',
        component: () => import('../views/content/ContentList.vue'),
        meta: { title: '内容管理' }
      },
      {
        path: 'content/upload',
        name: 'ContentUpload',
        component: () => import('../views/content/ContentUpload.vue'),
        meta: { title: '上传内容' }
      },
      {
        path: 'content/edit',
        name: 'ContentEdit',
        component: () => import('../views/content/ContentEdit.vue'),
        meta: { title: '编辑内容' }
      },
      {
        path: 'review',
        name: 'ReviewManagement',
        component: () => import('../views/review/ReviewQueue.vue'),
        meta: { title: '审核队列' }
      },
      {
        path: 'review/expert',
        name: 'ExpertReview',
        component: () => import('../views/review/ExpertReview.vue'),
        meta: { title: '专家审核' }
      },

      {
        path: 'tags',
        name: 'TagManagement',
        component: () => import('../views/tags/TagList.vue'),
        meta: { title: '标签管理' }
      },
      {
        path: 'categories',
        name: 'CategoryManagement',
        component: () => import('../views/categories/CategoryList.vue'),
        meta: { title: '分类管理' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('../views/users/UserList.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'kols',
        name: 'KOLManagement',
        component: () => import('../views/kols/KOLList.vue'),
        meta: { title: 'KOL管理' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('../views/analytics/ContentAnalytics.vue'),
        meta: { title: '内容分析' }
      },
      {
        path: 'analytics/interactions',
        name: 'UserInteractions',
        component: () => import('../views/analytics/UserInteractions.vue'),
        meta: { title: '用户互动管理' }
      },
      {
        path: 'analytics/reports',
        name: 'ReportManagement',
        component: () => import('../views/analytics/ReportManagement.vue'),
        meta: { title: '举报管理' }
      },
      {
        path: 'change-password',
        name: 'ChangePassword',
        component: () => import('../views/ChangePassword.vue'),
        meta: { title: '修改密码' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 认证检查
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('admin_token')
  
  if (!to.meta.noAuth && !token) {
    next('/login')
  } else {
    // 设置页面标题
    document.title = to.meta.title ? `${to.meta.title} - 企业视频平台管理后台` : '企业视频平台管理后台'
    
    // 如果有token但没有用户信息，从后端获取
    if (token && to.path !== '/login') {
      const { useUserStore } = await import('../stores/user')
      const userStore = useUserStore()
      
      if (!userStore.userInfo) {
        await userStore.fetchUserInfo()
      }
    }
    
    next()
  }
})

export default router

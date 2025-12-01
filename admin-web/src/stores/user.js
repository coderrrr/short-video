import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const userInfo = ref(null)

  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('admin_token', newToken)
  }

  const setUserInfo = (info) => {
    userInfo.value = info
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('admin_token')
  }

  // 从后端获取用户信息
  const fetchUserInfo = async () => {
    if (!token.value) return
    
    try {
      const { getCurrentUser } = await import('@/api/auth')
      const user = await getCurrentUser()
      setUserInfo(user)
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果token无效，清除并跳转登录
      if (error.response?.status === 401) {
        logout()
      }
    }
  }

  return {
    token,
    userInfo,
    setToken,
    setUserInfo,
    logout,
    fetchUserInfo
  }
})

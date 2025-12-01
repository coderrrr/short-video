<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>企业视频平台管理后台</h2>
      <el-form :model="loginForm" label-width="80px">
        <el-form-item label="员工ID">
          <el-input 
            v-model="loginForm.username" 
            placeholder="请输入员工ID"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleLogin" 
            :loading="loading"
            style="width: 100%"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
        <div class="login-tips">
          <p>默认管理员账号：ADMIN001</p>
          <p>默认密码：admin123</p>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const loginForm = ref({
  username: '',
  password: ''
})

const loading = ref(false)

const handleLogin = async () => {
  // 验证表单
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.error('请输入员工ID和密码')
    return
  }

  loading.value = true
  
  try {
    // 调用后端登录API
    const response = await login({
      employee_id: loginForm.value.username,
      password: loginForm.value.password
    })
    
    // 保存token和用户信息
    userStore.setToken(response.access_token)
    userStore.setUserInfo(response.user)
    
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查员工ID和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.login-card {
  width: 400px;
  padding: 20px;
}

h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.login-tips {
  margin-top: 20px;
  padding: 10px;
  background-color: #f0f9ff;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  text-align: center;
}

.login-tips p {
  margin: 5px 0;
}
</style>

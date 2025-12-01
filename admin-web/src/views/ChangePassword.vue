<template>
  <div class="change-password-container">
    <el-card class="password-card">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>

      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="120px"
        class="password-form"
      >
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            确认修改
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div class="security-tips">
        <h4>密码安全提示</h4>
        <ul>
          <li>密码长度至少6位</li>
          <li>建议使用字母、数字和特殊字符的组合</li>
          <li>不要使用过于简单的密码</li>
          <li>定期更换密码以保证账号安全</li>
        </ul>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import request from '../api/request'

const router = useRouter()
const passwordFormRef = ref(null)
const loading = ref(false)

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 验证确认密码
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'))
  } else if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await request.post('/users/me/change-password', {
          old_password: passwordForm.oldPassword,
          new_password: passwordForm.newPassword,
          confirm_password: passwordForm.confirmPassword
        })

        ElMessage.success('密码修改成功，请重新登录')
        
        // 清除本地存储的 token
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        
        // 跳转到登录页
        setTimeout(() => {
          router.push('/login')
        }, 1500)
      } catch (error) {
        console.error('修改密码错误:', error)
        // 拦截器已经处理了 401、422、500 等错误
        // 这里只处理其他未被拦截器处理的错误
        const status = error.response?.status
        if (status && ![401, 422, 500].includes(status)) {
          const errorMessage = error.response?.data?.detail || 
                              error.response?.data?.message || 
                              '密码修改失败'
          ElMessage.error(errorMessage)
        }
      } finally {
        loading.value = false
      }
    }
  })
}

const handleReset = () => {
  passwordFormRef.value?.resetFields()
}
</script>

<style scoped>
.change-password-container {
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: calc(100vh - 100px);
}

.password-card {
  width: 100%;
  max-width: 600px;
  margin-top: 50px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.password-form {
  margin-top: 20px;
}

.security-tips {
  margin-top: 30px;
  padding: 15px;
  background-color: #f4f4f5;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.security-tips h4 {
  margin: 0 0 10px 0;
  color: #409eff;
  font-size: 14px;
}

.security-tips ul {
  margin: 0;
  padding-left: 20px;
}

.security-tips li {
  margin: 5px 0;
  color: #606266;
  font-size: 13px;
}
</style>

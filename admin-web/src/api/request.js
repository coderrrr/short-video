import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import router from '../router'
import { performanceMonitor, requestCache } from '../utils/performance'

// 创建 axios 实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    
    // 添加认证 token
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    
    // 记录请求开始时间
    config.metadata = { startTime: performance.now() }
    
    // 缓存已禁用
    // if (config.method === 'get' && config.cache !== false) {
    //   const cached = requestCache.get(config.url, config.params)
    //   if (cached) {
    //     console.log(`[API Cache Hit] ${config.url}`)
    //     return Promise.reject({ 
    //       __cached: true, 
    //       data: cached 
    //     })
    //   }
    // }
    
    // 记录请求日志
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
      params: config.params,
      data: config.data
    })
    
    return config
  },
  (error) => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    // 计算请求耗时
    const duration = performance.now() - response.config.metadata.startTime
    performanceMonitor.recordApiCall(response.config.url, duration)
    
    // 记录响应日志
    console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
      status: response.status,
      duration: `${duration.toFixed(2)}ms`,
      data: response.data
    })
    
    // 缓存已禁用
    // if (response.config.method === 'get' && response.config.cache !== false) {
    //   requestCache.set(response.config.url, response.config.params, response.data)
    // }
    
    return response.data
  },
  (error) => {
    // 处理缓存命中
    if (error.__cached) {
      return Promise.resolve(error.data)
    }
    
    console.error('[API Response Error]', error)
    
    // 处理不同的错误状态码
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 未认证
          // 如果是登录请求，不显示"登录已过期"，让调用方处理
          if (!error.config.url.includes('/login')) {
            // 对于修改密码等需要认证的接口，如果返回401说明token过期
            if (error.config.url.includes('/change-password')) {
              ElMessage.error('登录已过期，请重新登录')
            } else {
              ElMessage.error('登录已过期，请重新登录')
            }
            const userStore = useUserStore()
            userStore.logout()
            router.push('/login')
          }
          break
          
        case 403:
          // 无权限 - 不在拦截器中显示，让调用方处理
          break
          
        case 404:
          // 资源不存在 - 不在拦截器中显示，让调用方处理
          break
          
        case 400:
          // 请求参数错误 - 不在拦截器中显示，让调用方处理
          break
          
        case 422:
          // 验证错误 - 格式化显示验证错误信息
          if (Array.isArray(data.detail)) {
            // FastAPI 验证错误格式
            const errorMessages = data.detail.map(err => {
              const field = err.loc ? err.loc[err.loc.length - 1] : '字段'
              return `${field}: ${err.msg}`
            }).join('; ')
            ElMessage.error(errorMessages)
          } else if (typeof data.detail === 'string') {
            ElMessage.error(data.detail)
          } else {
            ElMessage.error(data.message || '请求参数验证失败')
          }
          break
          
        case 500:
          // 服务器错误
          ElMessage.error(data.detail || data.message || '服务器错误，请稍后重试')
          break
          
        default:
          // 其他5xx错误
          if (status >= 500) {
            ElMessage.error(data.detail || data.message || `服务器错误 (${status})`)
          }
          // 4xx错误让调用方处理
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      // 请求配置出错
      ElMessage.error('请求配置错误')
    }
    
    return Promise.reject(error)
  }
)

export default request

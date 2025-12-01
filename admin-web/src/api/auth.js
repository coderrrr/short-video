import request from './request'

/**
 * 认证相关 API
 */

// 管理员登录
export const login = (data) => {
  return request({
    url: '/users/admin-login',
    method: 'post',
    data
  })
}

// 获取当前用户信息
export const getCurrentUser = () => {
  return request({
    url: '/users/me',
    method: 'get'
  })
}

// 登出（前端处理，清除token）
export const logout = () => {
  // 后端暂无登出接口，前端直接清除token
  return Promise.resolve({ success: true })
}

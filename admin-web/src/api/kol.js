import request from './request'

/**
 * KOL管理相关 API
 */

// 获取KOL列表
export const getKOLList = (params) => {
  return request({
    url: '/admin/kols',
    method: 'get',
    params,
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

// 获取KOL详情
export const getKOLDetail = (id) => {
  return request({
    url: `/admin/kols/${id}`,
    method: 'get'
  })
}

// 创建KOL账号
export const createKOL = (data) => {
  return request({
    url: '/admin/kols',
    method: 'post',
    data
  })
}

// 撤销KOL状态
export const revokeKOL = (id) => {
  return request({
    url: `/admin/kols/${id}`,
    method: 'delete'
  })
}

// 搜索用户（用于选择KOL候选人）
export const searchUsers = (params) => {
  return request({
    url: '/users/search',
    method: 'get',
    params
  })
}

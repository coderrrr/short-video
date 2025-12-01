import request from './request'

/**
 * 仪表盘统计相关 API
 */

// 获取仪表盘统计数据
export const getDashboardStats = () => {
  return request({
    url: '/admin/analytics/dashboard',
    method: 'get',
    cache: false
  })
}

// 获取热门内容排行
export const getTopContents = (params) => {
  return request({
    url: '/admin/analytics/top-contents',
    method: 'get',
    params,
    cache: false
  })
}

// 获取活跃用户排行
export const getTopUsers = (params) => {
  return request({
    url: '/admin/analytics/top-users',
    method: 'get',
    params,
    cache: false
  })
}

// 获取趋势数据
export const getTrendData = (params) => {
  return request({
    url: '/admin/analytics/trends',
    method: 'get',
    params,
    cache: false
  })
}

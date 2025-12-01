import request from './request'

/**
 * 举报管理相关 API
 */

// 获取举报列表
export const getReportList = (params) => {
  return request({
    url: '/reports',
    method: 'get',
    params,
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

// 获取举报详情
export const getReportDetail = (reportId) => {
  return request({
    url: `/reports/${reportId}`,
    method: 'get'
  })
}

// 获取内容的举报记录
export const getContentReports = (contentId, params) => {
  return request({
    url: `/reports/content/${contentId}/reports`,
    method: 'get',
    params
  })
}

// 更新举报状态
export const updateReportStatus = (reportId, data) => {
  return request({
    url: `/reports/${reportId}`,
    method: 'put',
    data
  })
}

// 获取举报统计信息
export const getReportStatistics = () => {
  return request({
    url: '/reports/statistics/summary',
    method: 'get',
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

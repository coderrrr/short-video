import request from './request'

/**
 * 数据分析相关 API
 */

// 获取内容分析汇总和列表
export const getContentAnalyticsSummary = (params) => {
  return request({
    url: '/admin/analytics/content/summary',
    method: 'get',
    params
  })
}

// 获取特定内容的详细分析
export const getContentDetailedAnalytics = (contentId) => {
  return request({
    url: `/admin/analytics/content/${contentId}`,
    method: 'get'
  })
}

// 导出内容分析报告
export const exportAnalyticsReport = (data) => {
  return request({
    url: '/admin/analytics/content/export',
    method: 'post',
    data,
    responseType: 'blob'
  })
}

// 获取收藏记录
export const getFavoriteRecords = (params) => {
  return request({
    url: '/admin/analytics/interactions/favorites',
    method: 'get',
    params
  })
}

// 获取点赞记录
export const getLikeRecords = (params) => {
  return request({
    url: '/admin/analytics/interactions/likes',
    method: 'get',
    params
  })
}

// 获取标记记录
export const getBookmarkRecords = (params) => {
  return request({
    url: '/admin/analytics/interactions/bookmarks',
    method: 'get',
    params
  })
}

// 获取评论记录
export const getCommentRecords = (params) => {
  return request({
    url: '/admin/analytics/comments',
    method: 'get',
    params
  })
}

// 删除评论
export const deleteComment = (commentId) => {
  return request({
    url: `/admin/analytics/comments/${commentId}`,
    method: 'delete'
  })
}

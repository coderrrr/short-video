import request from './request'

/**
 * 内容管理相关 API
 */

// 获取内容列表
export const getContentList = (params) => {
  return request({
    url: '/admin/contents/list',
    method: 'get',
    params,
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

// 获取内容详情
export const getContentDetail = (id) => {
  return request({
    url: `/admin/contents/${id}/detail`,
    method: 'get'
  })
}

// 创建内容（提交表单数据）
export const uploadContent = (data) => {
  return request({
    url: '/admin/contents',
    method: 'post',
    data
  })
}

// 更新内容
export const updateContent = (id, data) => {
  return request({
    url: `/admin/contents/${id}`,
    method: 'put',
    data
  })
}

// 删除内容
export const deleteContent = (id) => {
  return request({
    url: `/admin/contents/${id}`,
    method: 'delete'
  })
}

// 批量删除内容
export const batchDeleteContent = (ids) => {
  return request({
    url: '/admin/contents/batch-delete',
    method: 'post',
    data: { 
      content_ids: ids,
      reason: '管理员批量删除'
    }
  })
}

// 下架内容
export const removeContent = (id, reason) => {
  return request({
    url: `/admin/contents/${id}/remove`,
    method: 'post',
    data: { reason }
  })
}

// 批量下架内容
export const batchRemoveContent = (ids, reason) => {
  return request({
    url: '/admin/contents/batch-remove',
    method: 'post',
    data: {
      content_ids: ids,
      reason: reason || '管理员批量下架',
      create_audit_log: true
    }
  })
}

// 恢复内容
export const restoreContent = (id) => {
  return request({
    url: `/admin/contents/${id}/restore`,
    method: 'post'
  })
}

// 设置精选内容
export const setFeaturedContent = (id, featured) => {
  return request({
    url: `/admin/contents/${id}/featured`,
    method: 'put',
    data: { featured }
  })
}

// 获取内容的评论列表
export const getContentComments = (contentId, params) => {
  return request({
    url: `/comments/content/${contentId}`,
    method: 'get',
    params,
    cache: false
  })
}

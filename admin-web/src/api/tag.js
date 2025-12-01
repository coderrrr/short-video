import request from './request'

/**
 * 标签管理相关 API
 */

// 获取标签列表
export const getTagList = (params) => {
  return request({
    url: '/admin/tags',
    method: 'get',
    params,
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

// 获取标签树
export const getTagTree = (params) => {
  return request({
    url: '/admin/tags/tree',
    method: 'get',
    params,
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

// 获取标签详情
export const getTagDetail = (id) => {
  return request({
    url: `/admin/tags/${id}`,
    method: 'get'
  })
}

// 创建标签
export const createTag = (data) => {
  return request({
    url: '/admin/tags',
    method: 'post',
    data
  })
}

// 更新标签
export const updateTag = (id, data) => {
  return request({
    url: `/admin/tags/${id}`,
    method: 'put',
    data
  })
}

// 删除标签
export const deleteTag = (id, params) => {
  return request({
    url: `/admin/tags/${id}`,
    method: 'delete',
    params
  })
}

// 批量分配标签
export const batchAssignTags = (data) => {
  return request({
    url: '/admin/tags/batch-assign',
    method: 'post',
    data
  })
}

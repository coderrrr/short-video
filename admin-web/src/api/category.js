import request from './request'

/**
 * 分类管理相关 API
 */

// 获取分类列表（树形结构）
export const getCategoryTree = () => {
  return request({
    url: '/admin/categories/tree',
    method: 'get',
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

// 获取分类列表
export const getCategoryList = (params) => {
  return request({
    url: '/admin/categories',
    method: 'get',
    params,
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

// 创建分类
export const createCategory = (data) => {
  return request({
    url: '/admin/categories',
    method: 'post',
    data
  })
}

// 更新分类
export const updateCategory = (id, data) => {
  return request({
    url: `/admin/categories/${id}`,
    method: 'put',
    data
  })
}

// 删除分类
export const deleteCategory = (id) => {
  return request({
    url: `/admin/categories/${id}`,
    method: 'delete'
  })
}

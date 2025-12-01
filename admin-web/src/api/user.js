/**
 * 用户管理 API
 */
import request from './request'

/**
 * 获取用户列表
 */
export function getUserList(params) {
  return request({
    url: '/users/',
    method: 'get',
    params
  })
}

/**
 * 搜索用户
 */
export function searchUsers(params) {
  return request({
    url: '/users/search',
    method: 'get',
    params
  })
}

/**
 * 获取用户详情
 */
export function getUserDetail(userId) {
  return request({
    url: `/users/${userId}`,
    method: 'get'
  })
}

/**
 * 创建用户
 */
export function createUser(data) {
  return request({
    url: '/users/',
    method: 'post',
    data
  })
}

/**
 * 更新用户信息
 */
export function updateUser(userId, data) {
  return request({
    url: `/users/${userId}`,
    method: 'put',
    data
  })
}

/**
 * 删除用户
 */
export function deleteUser(userId) {
  return request({
    url: `/users/${userId}`,
    method: 'delete'
  })
}

/**
 * 更新用户KOL状态
 */
export function updateUserKolStatus(userId, data) {
  return request({
    url: `/users/${userId}/kol-status`,
    method: 'put',
    data
  })
}

/**
 * 更新用户管理员状态
 */
export function updateUserAdminStatus(userId, data) {
  return request({
    url: `/users/${userId}/admin-status`,
    method: 'put',
    data
  })
}

/**
 * 获取用户关注数和粉丝数
 */
export function getUserFollowCounts(userId) {
  return request({
    url: `/users/${userId}/follow-counts`,
    method: 'get'
  })
}

/**
 * 获取用户的内容列表
 */
export function getUserContents(userId, params) {
  return request({
    url: `/users/${userId}/contents`,
    method: 'get',
    params
  })
}

/**
 * 获取创作者个人资料
 */
export function getCreatorProfile(userId) {
  return request({
    url: `/users/${userId}/profile`,
    method: 'get'
  })
}

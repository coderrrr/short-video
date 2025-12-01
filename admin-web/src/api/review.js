/**
 * 审核管理API
 */
import request from './request'

/**
 * 获取审核队列
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @param {string} params.content_type - 内容类型筛选
 * @param {string} params.creator_id - 创作者ID筛选
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @returns {Promise}
 */
export function getReviewQueue(params) {
  return request({
    url: '/admin/reviews/queue',
    method: 'get',
    params,
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

/**
 * 获取内容审核详情
 * @param {string} contentId - 内容ID
 * @returns {Promise}
 */
export function getContentReviewDetail(contentId) {
  return request({
    url: `/admin/reviews/${contentId}/detail`,
    method: 'get'
  })
}

/**
 * 批准内容
 * @param {Object} data - 批准数据
 * @param {string} data.content_id - 内容ID
 * @param {string} data.comment - 审核备注
 * @returns {Promise}
 */
export function approveContent(data) {
  return request({
    url: '/admin/reviews/approve',
    method: 'post',
    data
  })
}

/**
 * 拒绝内容
 * @param {Object} data - 拒绝数据
 * @param {string} data.content_id - 内容ID
 * @param {string} data.reason - 拒绝原因
 * @returns {Promise}
 */
export function rejectContent(data) {
  return request({
    url: '/admin/reviews/reject',
    method: 'post',
    data
  })
}

/**
 * 批量审核
 * @param {Object} data - 批量审核数据
 * @param {Array<string>} data.content_ids - 内容ID列表
 * @param {string} data.action - 操作类型（approve或reject）
 * @param {string} data.reason - 拒绝原因（action为reject时必填）
 * @returns {Promise}
 */
export function batchReview(data) {
  return request({
    url: '/admin/reviews/batch',
    method: 'post',
    data
  })
}

/**
 * 获取审核统计信息
 * @returns {Promise}
 */
export function getReviewStatistics() {
  return request({
    url: '/admin/reviews/statistics',
    method: 'get',
    cache: false  // 禁用缓存，确保获取最新数据
  })
}

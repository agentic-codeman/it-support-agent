/**
 * Query Term Mapping (关键词映射) API 服务
 */
import api from './api';

const MAPPING_BASE_URL = '/mappings';

export const mappingService = {
  /**
   * 分页查询关键词映射规则
   */
  async pageQuery(current = 1, size = 10, keyword = undefined) {
    const params = { current, size };
    if (keyword) {
      params.keyword = keyword;
    }
    const response = await api.get(MAPPING_BASE_URL, { params });
    return response.data?.data || response.data;
  },

  /**
   * 查询关键词映射规则详情
   */
  async getById(id) {
    const response = await api.get(`${MAPPING_BASE_URL}/${id}`);
    return response.data?.data || response.data;
  },

  /**
   * 创建关键词映射规则
   */
  async create(data) {
    const response = await api.post(MAPPING_BASE_URL, data);
    return response.data?.data || response.data;
  },

  /**
   * 更新关键词映射规则
   */
  async update(id, data) {
    const response = await api.put(`${MAPPING_BASE_URL}/${id}`, data);
    return response.data;
  },

  /**
   * 删除关键词映射规则
   */
  async delete(id) {
    const response = await api.delete(`${MAPPING_BASE_URL}/${id}`);
    return response.data;
  },
};

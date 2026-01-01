/**
 * Web Search API 客户端
 */
import axios from 'axios';
import type {
  SearchRequest,
  SearchResponse,
  AnswerResponse,
  SearchUsage,
  WebSearchStatus,
  FetchRequest,
  FetchResponse,
  ExtractRequest,
  ExtractResponse,
  CacheStats,
} from '@/types/web-search';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const webSearchApi = {
  /**
   * 执行网络搜索
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    const { data } = await axios.post<SearchResponse>(
      `${API_BASE_URL}/api/web-search/search`,
      request
    );
    return data;
  },

  /**
   * 获取 AI 生成的答案
   */
  async getAnswer(query: string, searchDepth: 'basic' | 'advanced' = 'basic'): Promise<AnswerResponse> {
    const { data } = await axios.post<AnswerResponse>(
      `${API_BASE_URL}/api/web-search/answer`,
      { query, search_depth: searchDepth }
    );
    return data;
  },

  /**
   * 获取使用统计
   */
  async getUsage(): Promise<SearchUsage> {
    const { data } = await axios.get<SearchUsage>(
      `${API_BASE_URL}/api/web-search/usage`
    );
    return data;
  },

  /**
   * 检查限流状态
   */
  async checkLimit(): Promise<{ can_search: boolean; used: number; limit: number; remaining: number }> {
    const { data } = await axios.get(
      `${API_BASE_URL}/api/web-search/check-limit`
    );
    return data;
  },

  /**
   * 获取服务状态
   */
  async getStatus(): Promise<WebSearchStatus> {
    const { data } = await axios.get<WebSearchStatus>(
      `${API_BASE_URL}/api/web-search/status`
    );
    return data;
  },

  // ========== 新增：内容获取 API ==========

  /**
   * 获取网页内容（多级回退）
   */
  async fetchPage(request: FetchRequest): Promise<FetchResponse> {
    const { data } = await axios.post<FetchResponse>(
      `${API_BASE_URL}/api/web-search/fetch`,
      request
    );
    return data;
  },

  /**
   * 批量获取网页内容
   */
  async batchFetch(urls: string[], maxConcurrent: number = 3): Promise<{
    success: boolean;
    results: Array<FetchResponse | { url: string; error: string }>;
    total: number;
    succeeded: number;
    failed: number;
  }> {
    const { data } = await axios.post(
      `${API_BASE_URL}/api/web-search/batch-fetch`,
      null,
      {
        params: {
          urls: urls.join(','),
          max_concurrent: maxConcurrent,
        },
      }
    );
    return data;
  },

  // ========== 新增：内容提取 API ==========

  /**
   * 使用 AI 提取内容关键信息
   */
  async extractContent(request: ExtractRequest): Promise<ExtractResponse> {
    const { data } = await axios.post<ExtractResponse>(
      `${API_BASE_URL}/api/web-search/extract`,
      request
    );
    return data;
  },

  // ========== 新增：缓存管理 API ==========

  /**
   * 获取缓存统计
   */
  async getCacheStats(): Promise<CacheStats> {
    const { data } = await axios.get<CacheStats>(
      `${API_BASE_URL}/api/web-search/cache/stats`
    );
    return data;
  },

  /**
   * 清空缓存
   */
  async clearCache(): Promise<{ success: boolean; message: string }> {
    const { data } = await axios.post(
      `${API_BASE_URL}/api/web-search/cache/clear`
    );
    return data;
  },
};

// 简化的搜索函数（使用默认用户ID）
export async function webSearch(query: string, maxResults: number = 5): Promise<SearchResponse> {
  return webSearchApi.search({
    query,
    max_results: maxResults,
    user_id: 'anonymous',
  });
}

// 获取答案的简化函数
export async function getSearchAnswer(query: string): Promise<string> {
  const response = await webSearchApi.getAnswer(query);
  return response.answer;
}

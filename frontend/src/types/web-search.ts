/**
 * Web Search 类型定义
 */

export interface SearchResult {
  title: string;
  url: string;
  content: string;
  score?: number;
  publishedDate?: string;
}

export interface SearchUsage {
  used: number;
  limit: number;
  remaining: number;
  unique_users_today?: number;
  reset_at?: string;
}

export interface SearchResponse {
  success: boolean;
  query: string;
  results: SearchResult[];
  count: number;
  usage: SearchUsage;
  error?: string;
  message?: string;
}

export interface AnswerResponse {
  success: boolean;
  query: string;
  answer: string;
}

export interface SearchRequest {
  query: string;
  max_results?: number;
  search_depth?: 'basic' | 'advanced';
  include_domains?: string[];
  exclude_domains?: string[];
  user_id: string;
}

export interface WebSearchStatus {
  tavily_available: boolean;
  daily_limit: number;
  enabled: boolean;
}

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

// 新增：内容获取相关类型
export interface PageContent {
  url: string;
  title: string;
  content: string;
  author?: string;
  date?: string;
  source: 'cache' | 'direct' | 'jina' | 'archive';
  fetched_at?: string;
}

export interface FetchRequest {
  url: string;
  force_refresh?: boolean;
}

export interface FetchResponse {
  success: boolean;
  url: string;
  title: string;
  content: string;
  author?: string;
  date?: string;
  source: 'cache' | 'direct' | 'jina' | 'archive';
  fetched_at?: string;
}

// 新增：内容提取相关类型
export interface ExtractedContent {
  title: string;
  summary: string;
  key_points: string[];
  relevance_score: number;
  confidence: number;
}

export interface ExtractRequest {
  content: string;
  query: string;
  url?: string;
}

export interface ExtractResponse {
  success: boolean;
  title: string;
  summary: string;
  key_points: string[];
  relevance_score: number;
  confidence: number;
}

// 新增：缓存相关类型
export interface CacheStats {
  size: number;
  max_size: number;
  ttl: number;
  usage_percent: number;
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

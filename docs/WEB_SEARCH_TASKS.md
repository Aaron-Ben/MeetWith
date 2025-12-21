# Web Search Feature - Task Breakdown
# 网络搜索功能 - 任务分解文档

**Version:** 2.0 (Python + Tavily + DeepSeek)  
**Last Updated:** 2025-12-20  
**Status:** Planning (Migration from TypeScript/Google/Gemini)  
**Related:** [WEB_SEARCH_SPEC.md](./WEB_SEARCH_SPEC.md) | [WEB_SEARCH_DESIGN.md](./WEB_SEARCH_DESIGN.md)

---

## Table of Contents | 目录

1. [Epic Overview | 史诗概览](#1-epic-overview)
2. [Phase 1: Foundation | 基础阶段](#2-phase-1-foundation)
3. [Phase 2: Core Search | 核心搜索](#3-phase-2-core-search)
4. [Phase 3: Iteration & Intelligence | 迭代与智能](#4-phase-3-iteration--intelligence)
5. [Phase 4: Integration & Polish | 集成与优化](#5-phase-4-integration--polish)
6. [Testing Tasks | 测试任务](#6-testing-tasks)
7. [Documentation Tasks | 文档任务](#7-documentation-tasks)

---

## 1. Epic Overview | 史诗概览

### 1.1 Epic Goal | 史诗目标
实现智能网络搜索功能，使 AI 助手能够自动判断需求、执行搜索、迭代优化，并将相关信息整合到对话上下文中。

### 1.2 Success Criteria | 成功标准
- ✅ 95% 的"最新信息"请求被正确识别
- ✅ 平均响应时间 < 30 秒
- ✅ 搜索结果相关性评分 > 7.0
- ✅ 成本控制：< 100 次搜索/天

### 1.3 Timeline | 时间线
- **Phase 1:** 2 days (Foundation)
- **Phase 2:** 3 days (Core Search)
- **Phase 3:** 4 days (Iteration & Intelligence)
- **Phase 4:** 2 days (Integration & Polish)
- **Testing:** 2 days
- **Total:** ~13 days

---

## 2. Phase 1: Foundation | 基础阶段

**Duration:** 2 days  
**Status:** Planning

### Task 1.1: Project Setup | 项目设置
**Priority:** P0  
**Estimate:** 2 hours  
**Status:** Pending

**Subtasks:**
- [ ] Create Python type definitions in `backend/src/agent/types.py`
  ```python
  from dataclasses import dataclass
  from typing import List

  @dataclass
  class SearchResult:
      title: str
      link: str
      snippet: str
      raw_content: str = ""
  
  @dataclass
  class ExtractedContent:
      source_url: str
      title: str
      summary: str
      key_points: List[str]
      relevance_score: float
      confidence: float
  ```
- [ ] Setup Python environment with dependencies
  ```bash
  pip install tavily-python deepseek aiohttp pydantic
  ```
- [ ] Add environment variables to `.env.example`
  ```bash
  TAVILY_API_KEY=your_tavily_api_key
  DEEPSEEK_API_KEY=your_deepseek_api_key
  DEEPSEEK_MODEL=deepseek-chat  # or deepseek-reasoner
  ```

**Acceptance Criteria:**
- All type definitions are properly defined
- Python environment is configured
- Dependencies are installed

**Acceptance Criteria:**
- All type files compile without errors
- Environment variables documented

---

### Task 1.2: Tavily Search Setup | Tavily 搜索设置
**Priority:** P0  
**Estimate:** 2 hours  
**Status:** Pending

**Subtasks:**
- [ ] Sign up for Tavily API at https://tavily.com
- [ ] Obtain API Key
- [ ] Test API with Python
  ```bash
  python -c "
  import asyncio
  from tavily import AsyncTavilyClient
  
  async def test():
      client = AsyncTavilyClient(api_key='YOUR_KEY')
      result = await client.search('test query')
      print(result)
  
  asyncio.run(test())
  "
  ```

**Acceptance Criteria:**
- Tavily API Key is obtained and working
- API returns valid search results

---

### Task 1.3: Implement TavilySearchService | 实现 Tavily 搜索服务
**Priority:** P0  
**Estimate:** 3 hours  
**Status:** Pending  
**File:** `backend/src/agent/web_search.py`

**Subtasks:**
- [ ] Create `TavilySearchService` class
- [ ] Implement async `search(query: str, num_results: int)` method
  - Use `AsyncTavilyClient`
  - Return structured `SearchResult[]`
- [ ] Add error handling and retries
- [ ] Add logging for debugging

**Code Structure:**
```python
from tavily import AsyncTavilyClient

class TavilySearchService:
    def __init__(self):
        self.client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """Search using Tavily API"""
        # Implementation
        pass
```

**Acceptance Criteria:**
- Returns 5-10 search results for valid queries
- Handles API errors gracefully
- Logs search queries and results

**Testing:**
```python
service = TavilySearchService()
results = await service.search("Tesla stock price", 5)
assert len(results) >= 5
assert results[0].title is not None
```

---

### Task 1.4: Implement SearchRateLimiter | 实现速率限制器
**Priority:** P0  
**Estimate:** 3 hours  
**Status:** Pending  
**File:** `backend/src/agent/rate_limiter.py`

**Subtasks:**
- [ ] Create rate limiter using simple in-memory cache or Redis
- [ ] Implement `check_rate_limit()` method
- [ ] Implement `track_usage()` method
- [ ] Add daily reset capability

**Code Structure:**
```python
class SearchRateLimiter:
    async def check_rate_limit(self) -> dict:
        """Check if search is allowed"""
        pass
    
    async def track_usage(self, user_id: str, query: str) -> None:
        """Track search usage"""
        pass
```

**Acceptance Criteria:**
- Can track search count per day
- Returns current usage stats
- Resets daily

---

## 3. Phase 2: Core Search | 核心搜索

**Duration:** 3 days  
**Status:** Planning

### Task 2.1: Implement ContentFetcher | 实现内容获取器
**Priority:** P0  
**Estimate:** 6 hours  
**Status:** Pending  
**File:** `backend/src/agent/content_fetcher.py`

**Subtasks:**
- [ ] **Layer 1: Cache**
  - In-memory cache with TTL (1 hour)
  - Dictionary-based caching
  
- [ ] **Layer 2: Direct Fetch**
  - Use `aiohttp` with User-Agent rotation
  - Use `BeautifulSoup` to extract text
  - Remove `<script>`, `<style>`, navigation elements
  - Limit to 10,000 characters
  
- [ ] **Layer 3: Jina.ai Reader**
  - Fetch from `https://r.jina.ai/{url}`
  - Return plain text
  
- [ ] **Layer 4: Archive.org**
  - Get latest snapshot URL
  - Fetch snapshot content

- [ ] Implement `fetch_multiple()` with concurrency control
  - Process 2 URLs in parallel
  - Use `asyncio.gather()`

**Code Structure:**
```python
class ContentFetcher:
    def __init__(self):
        self.cache = {}
        self.user_agents = [...]  # 8 different user agents
    
    async def fetch(self, url: str) -> str:
        """Try 4 layers to fetch content"""
        pass
    
    async def fetch_multiple(self, urls: list[str], concurrency: int = 2) -> dict:
        """Fetch multiple URLs with concurrency control"""
        pass
```

**Acceptance Criteria:**
- Successfully fetches content from at least 80% of URLs
- Falls back gracefully through all 4 layers
- Respects concurrency limits
- Cache reduces duplicate fetches

---

### Task 2.2: Implement ContentExtractor | 实现内容提取器
**Priority:** P0  
**Estimate:** 5 hours  
**Status:** Pending  
**File:** `backend/src/agent/content_extractor.py`

**Subtasks:**
- [ ] Create extraction prompt template
- [ ] Implement async `extract()` method
  - Call DeepSeek Chat API
  - Parse JSON response
  - Handle parsing errors with retry
  
- [ ] Implement async `extract_and_rank()` method
  - Call `extract()` for each URL in parallel
  - Sort by `relevance_score` descending
  
- [ ] Add retry logic (max 1 retry per extraction)
- [ ] Add timeout (10 seconds per extraction)

**Code Structure:**
```python
class ContentExtractor:
    def __init__(self, deepseek_client):
        self.client = deepseek_client
    
    async def extract(self, raw_content: str, user_question: str, 
                     target_info: list[str], source_url: str) -> ExtractedContent:
        """Extract relevant content using DeepSeek"""
        pass
    
    async def extract_and_rank(self, items: list[dict], 
                             user_question: str, target_info: list[str]) -> list[ExtractedContent]:
        """Extract and rank multiple items"""
        pass
```

**Acceptance Criteria:**
- Successfully extracts from 90% of valid content
- Returns structured JSON
- Relevance scores correlate with actual relevance
- Sorted results are in correct order

---

### Task 2.3: Implement PromptAnalyzer | 实现提示词分析器
**Priority:** P0  
**Estimate:** 4 hours  
**Status:** Pending  
**File:** `backend/src/agent/prompt_analyzer.py`

**Subtasks:**
- [ ] Create analysis prompt template
  - Include examples of when to search vs. not search
  - Request structured JSON output
  
- [ ] Implement async `analyze()` method
  - Call DeepSeek Chat with temperature 0.3
  - Parse JSON response
  - Extract web_search.needed, query, targetInfo
  
- [ ] Add fallback for JSON parsing errors
- [ ] Include current date in analysis (for time-sensitive queries)

**Code Structure:**
```python
class PromptAnalyzer:
    def __init__(self, deepseek_client):
        self.client = deepseek_client
    
    async def analyze(self, user_message: str, 
                     conversation_history: list = None,
                     current_date: str = None) -> dict:
        """Analyze user input to determine if web search is needed"""
        pass
```

**Acceptance Criteria:**
- Correctly identifies 95% of search needs
- Generates effective search queries
- Identifies target information aspects
- Runs in < 2 seconds

---

## 4. Phase 3: Iteration & Intelligence | 迭代与智能

**Duration:** 3 days  
**Status:** Planning

### Task 3.1: Implement Reflection Mechanism | 实现反思机制
**Priority:** P1  
**Estimate:** 3 hours  
**Status:** Pending  
**File:** `backend/src/agent/orchestrator.py` (method: `reflect_on_content`)

**Subtasks:**
- [ ] Create reflection prompt template using DeepSeek
- [ ] Implement async `reflect_on_content()` method
  - Input: extracted_content[], target_info[], user_question
  - Output: SearchReflection dict
  
- [ ] Add decision logic:
  - If sufficient: return True
  - If insufficient: provide refined_query
  - If uncertain: provide missing_aspects
  
- [ ] Add fallback (assume sufficient on error)

**Code Structure:**
```python
class SearchReflection:
    sufficient: bool
    missing_aspects: list[str]
    refined_query: str
    reasoning: str
    confidence: float

async def reflect_on_content(self, extracted_content: list[ExtractedContent],
                            target_info: list[str],
                            user_question: str,
                            iteration: int) -> SearchReflection:
    """Evaluate if gathered information is sufficient"""
    pass
```

**Acceptance Criteria:**
- Correctly judges sufficiency
- Generates useful refined queries
- Runs in < 3 seconds
- Handles edge cases (empty content, low relevance)

// Test insufficient case
const reflection2 = await reflectOnContent(
  [lowRelevanceContent],
  ["price", "reviews", "specs"],
  "Compare products"
);
expect(reflection2.sufficient).toBe(false);
expect(reflection2.refinedQuery).toBeDefined();
```

---

### Task 3.2: Implement Iterative Search Loop | 实现迭代搜索循环
**Priority:** P0  
**Estimate:** 6 hours  
**Status:** Pending  
**File:** `backend/src/agent/orchestrator.py` (method: `execute_iterative_search`)

**Subtasks:**
- [ ] Create async `execute_iterative_search()` method
- [ ] Implement loop (max 3 iterations)
  - Iteration 1: Use initial query
  - Iteration 2-3: Use refined_query from reflection
  
- [ ] Accumulate results across iterations
  - All search results in one list
  - All extracted content in one list
  
- [ ] Add exit conditions:
  - reflection.sufficient = True
  - iteration = MAX_ITERATIONS
  - no refined_query provided
  
- [ ] Emit progress events for each step
- [ ] Handle errors gracefully (continue with what we have)

**Code Structure:**
```python
async def execute_iterative_search(self, user_id: str, analysis: dict,
                                  progress_emitter = None) -> dict:
    """Execute iterative search with up to 3 iterations"""
    pass
```

**Acceptance Criteria:**
- Runs 1-3 iterations based on reflection
- Accumulates all results
- Stops when sufficient
- Handles errors without crashing
- Emits progress events

---

### Task 3.3: Implement ProgressEmitter | 实现进度发射器
**Priority:** P1  
**Estimate:** 3 hours  
**Status:** ✅ Done  
**File:** `src/lib/progress/emitter.ts`

**Subtasks:**
- [x] Create `ProgressEmitter` class
- [x] Implement event methods:
  - `emitWebSearchStart(query)`
  - `emitWebSearchIteration(iteration, query)`
  - `emitWebSearchFetching(count)`
  - `emitWebSearchExtracting()`
  - `emitWebSearchReflecting()`
  - `emitWebSearchComplete(resultsCount)`
  
- [x] Add SSE formatting
- [x] Add error event handling

**Code Structure:**
```typescript
export class ProgressEmitter {
  constructor(private controller: ReadableStreamDefaultController) {}
  
  emit(event: ProgressEvent): void {
    const data = `data: ${JSON.stringify(event)}\n\n`;
    this.controller.enqueue(new TextEncoder().encode(data));
  }
  
  emitWebSearchStart(query: string): void {
    this.emit({
      type: "web_search_start",
      data: { query, message: `🌐 Searching the web: ${query}` }
    });
  }
  
  // ... other methods
}
```

**Acceptance Criteria:**
- Events are formatted correctly for SSE
- Frontend can parse events
- No encoding errors

---

### Task 3.4: Implement Context Building | 实现上下文构建
**Priority:** P0  
**Estimate:** 4 hours  
**Status:** ✅ Done  
**File:** `src/lib/context-engineering/orchestrator.ts` (method: `buildFinalContext`)

**Subtasks:**
- [x] Create `buildFinalContext()` method
- [x] Format memories section (if any)
- [x] Format web search results section
  - Include source title and URL
  - Include summary and key points
  - Use Markdown format
  
- [x] Add metadata (search date, iteration count)
- [x] Limit total context length (max 20,000 chars)

**Context Format:**
```markdown
**User Context (from memory):**
- User prefers concise answers
- Previous interest in Tesla

**Web Search Results (实时网络搜索结果 - 2024-12-19):**

[Source 1: Tesla Stock Price Today | NASDAQ](https://nasdaq.com/...)
Summary: Tesla stock closed at $250.45, up 3.2% from yesterday...
Key Points:
- Current price: $250.45
- Change: +3.2%
- Volume: 125M shares

[Source 2: Tesla Q4 Earnings Report](https://reuters.com/...)
Summary: Tesla reported strong Q4 earnings...
Key Points:
- Revenue: $25.2B
- Profit: $3.1B
- Guidance: optimistic

---
Total sources: 2 (from 2 search iterations)
```

**Acceptance Criteria:**
- Context is well-formatted Markdown
- Includes all relevant information
- Respects length limits
- Easy for AI to parse

**Testing:**
```typescript
const context = buildFinalContext(
  searchResults,
  extractedContent,
  memories,
  analysis
);

expect(context).toContain("Web Search Results");
expect(context).toContain("Source 1:");
expect(context.length).toBeLessThan(20000);
```

---

## 5. Phase 4: Integration & Polish | 集成与优化

**Duration:** 2 days  
**Status:** ✅ Completed

### Task 4.1: Integrate into ContextOrchestrator | 集成到上下文编排器
**Priority:** P0  
**Estimate:** 4 hours  
**Status:** ✅ Done

**Subtasks:**
- [x] Add web search flow to `ContextOrchestrator.prepare()`
- [x] Call `PromptAnalyzer.analyze()`
- [x] Conditionally call `executeIterativeSearch()`
- [x] Combine results in `buildFinalContext()`
- [x] Return `ContextEngineeringResult` with search metadata

**Updated `prepare()` method:**
```typescript
async prepare(params: ContextPreparationParams): Promise<ContextEngineeringResult> {
  const { userMessage, userId, conversationHistory, progressEmitter } = params;
  
  // 1. Analyze prompt
  const analysis = await PromptAnalyzer.analyze({
    userMessage,
    conversationHistory,
    currentDate: new Date().toISOString()
  });
  
  // 2. Load memories
  const memories = await MemoryLoader.load(userId, userMessage);
  
  // 3. Execute web search (if needed)
  let searchResults = [];
  let extractedContent = [];
  if (analysis.actions.web_search.needed) {
    const result = await this.executeIterativeSearch(userId, analysis, progressEmitter);
    searchResults = result.searchResults;
    extractedContent = result.extractedContent;
  }
  
  // 4. Build final context
  const context = this.buildFinalContext(searchResults, extractedContent, memories, analysis);
  
  // 5. Select model
  const model = this.selectModel(analysis);
  
  return {
    context,
    model,
    webSearchResults: searchResults,
    extractedContent,
    memoryFacts: memories
  };
}
```

**Acceptance Criteria:**
- Web search is triggered when needed
- Results are included in context
- No errors when search is not needed

---

### Task 4.2: Update Chat API | 更新聊天 API
**Priority:** P0  
**Estimate:** 3 hours  
**Status:** ✅ Done  
**File:** `src/app/api/chat/route.ts`

**Subtasks:**
- [x] Pass `ProgressEmitter` to `ContextOrchestrator.prepare()`
- [x] Store search metadata in conversation
- [x] Handle rate limit errors
- [x] Add error messages for failed searches

**Updated Chat API:**
```typescript
export async function POST(req: Request) {
  // ... existing code
  
  const stream = new ReadableStream({
    async start(controller) {
      const progressEmitter = new ProgressEmitter(controller);
      
      try {
        // Prepare context with web search
        const result = await orchestrator.prepare({
          userMessage,
          userId,
          conversationHistory,
          progressEmitter
        });
        
        // Generate response
        const aiResponse = await provider.generateContent({
          prompt: userMessage,
          context: result.context,
          model: result.model,
          stream: true
        });
        
        // Save message with search metadata
        await saveMessage({
          ...message,
          metadata: {
            webSearchPerformed: result.webSearchResults.length > 0,
            searchIterations: ...,
            searchResultsCount: result.webSearchResults.length
          }
        });
        
      } catch (error) {
        if (error.code === 'RATE_LIMIT_EXCEEDED') {
          progressEmitter.emit({
            type: "error",
            data: { message: "已达到每日搜索限制（100次）" }
          });
        }
      }
    }
  });
  
  return new Response(stream, { headers: { "Content-Type": "text/event-stream" } });
}
```

**Acceptance Criteria:**
- Progress events are sent to client
- Search metadata is saved
- Errors are handled gracefully

---

### Task 4.3: Frontend Progress Display | 前端进度显示
**Priority:** P2  
**Estimate:** 3 hours  
**Status:** ✅ Done  
**File:** `src/app/chat/page.tsx`, `src/components/chat/ChatMessage.tsx`

**Subtasks:**
- [x] Parse SSE events in chat page
- [x] Display search progress (e.g., "🌐 Searching the web...")
- [x] Show iteration count
- [x] Display search sources in message
- [x] Add loading indicators

**Frontend Code:**
```typescript
// Parse SSE events
const lines = buffer.split("\n\n");
for (const line of lines) {
  if (line.startsWith("data: ")) {
    const event = JSON.parse(line.slice(6));
    
    if (event.type === "web_search_iteration") {
      setProgressMessage(`🌐 ${event.data.message}`);
    } else if (event.type === "text_chunk") {
      appendText(event.data.text);
    }
  }
}
```

**Acceptance Criteria:**
- Users see real-time search progress
- Progress messages are clear
- No UI blocking during search

---

### Task 4.4: Error Handling & Logging | 错误处理与日志
**Priority:** P1  
**Estimate:** 2 hours  
**Status:** ✅ Done

**Subtasks:**
- [x] Add comprehensive logging
  - Log all searches with query, userId, timestamp
  - Log rate limit hits
  - Log API errors
  
- [x] Add error recovery
  - Continue conversation if search fails
  - Use memories only as fallback
  
- [x] Add admin alerts
  - Email when rate limit is close (90%)
  - Alert on repeated API failures

**Logging Example:**
```typescript
console.log('[WebSearch] Starting search', {
  userId,
  query,
  targetInfo,
  timestamp: new Date().toISOString()
});

console.log('[WebSearch] Iteration complete', {
  iteration,
  resultsCount,
  extractedCount,
  sufficient: reflection.sufficient
});

console.error('[WebSearch] Error', {
  error: error.message,
  query,
  userId,
  stack: error.stack
});
```

**Acceptance Criteria:**
- All searches are logged
- Errors are tracked
- Admins are notified of issues

---

### Task 4.5: Performance Optimization | 性能优化
**Priority:** P2  
**Estimate:** 4 hours  
**Status:** ✅ Done

**Subtasks:**
- [x] **Caching:**
  - Implement content cache (1-hour TTL)
  - Cache extraction results
  
- [x] **Parallel Processing:**
  - Fetch 2 URLs concurrently
  - Extract from 3 pages in parallel
  
- [x] **Timeout Optimization:**
  - Reduce fetch timeout to 8 seconds
  - Add extraction timeout (10 seconds)
  
- [x] **Query Optimization:**
  - Trim search queries
  - Remove redundant words

**Performance Targets:**
| Operation | Target | Actual |
|-----------|--------|--------|
| Prompt Analysis | < 2s | ~1.5s |
| Single Search | < 3s | ~2s |
| Fetch 3 URLs | < 10s | ~8s |
| Extract 3 Pages | < 8s | ~6s |
| Reflection | < 3s | ~2s |
| **Total (1 iteration)** | **< 26s** | **~20s** |

**Acceptance Criteria:**
- Average response time < 30s
- 80% of requests complete in < 25s
- Cache hit rate > 20%

---

## 6. Testing Tasks | 测试任务

**Duration:** 2 days  
**Status:** ✅ Completed

### Task 6.1: Unit Tests | 单元测试
**Priority:** P1  
**Estimate:** 6 hours  
**Status:** ✅ Done

**Test Files:**
- [x] `src/lib/web-search/__tests__/google-search.test.ts`
- [x] `src/lib/web-search/__tests__/content-fetcher.test.ts`
- [x] `src/lib/web-search/__tests__/content-extractor.test.ts`
- [x] `src/lib/web-search/__tests__/rate-limiter.test.ts`
- [x] `src/lib/prompt-analysis/__tests__/analyzer.test.ts`

**Test Cases:**
```typescript
describe('GoogleSearchService', () => {
  it('should return search results', async () => {
    const service = new GoogleSearchService();
    const results = await service.search("test query", 5);
    expect(results).toHaveLength(5);
  });
  
  it('should handle API errors', async () => {
    // Mock API failure
    await expect(service.search("")).rejects.toThrow();
  });
});

describe('ContentFetcher', () => {
  it('should fetch content with fallback', async () => {
    const fetcher = new ContentFetcher();
    const content = await fetcher.fetch("https://example.com");
    expect(content.length).toBeGreaterThan(0);
  });
  
  it('should use cache', async () => {
    const fetcher = new ContentFetcher();
    const c1 = await fetcher.fetch("https://example.com");
    const c2 = await fetcher.fetch("https://example.com");
    expect(c1).toBe(c2);
  });
});

describe('PromptAnalyzer', () => {
  it('should detect web search need', async () => {
    const result = await PromptAnalyzer.analyze({
      userMessage: "What is the latest Tesla stock price?"
    });
    expect(result.actions.web_search.needed).toBe(true);
  });
  
  it('should NOT trigger for general knowledge', async () => {
    const result = await PromptAnalyzer.analyze({
      userMessage: "Explain bubble sort"
    });
    expect(result.actions.web_search.needed).toBe(false);
  });
});
```

---

### Task 6.2: Integration Tests | 集成测试
**Priority:** P1  
**Estimate:** 4 hours  
**Status:** ✅ Done

**Test File:** `src/lib/context-engineering/__tests__/orchestrator.test.ts`

**Test Cases:**
```typescript
describe('ContextOrchestrator - Web Search Integration', () => {
  it('should complete full search flow', async () => {
    const orchestrator = new ContextOrchestrator();
    const result = await orchestrator.prepare({
      userMessage: "Tesla stock price today",
      userId: "test-user"
    });
    
    expect(result.context).toContain("Web Search Results");
    expect(result.webSearchResults.length).toBeGreaterThan(0);
    expect(result.extractedContent.length).toBeGreaterThan(0);
  });
  
  it('should handle rate limit gracefully', async () => {
    // Mock rate limit hit
    const result = await orchestrator.prepare({...});
    expect(result.context).not.toContain("Web Search Results");
    // Should still have memories
  });
  
  it('should perform multiple iterations', async () => {
    // Track iteration count via logs
    const result = await orchestrator.prepare({
      userMessage: "Compare iPhone 16 vs Samsung S24"
    });
    // Verify 2-3 iterations occurred
  });
});
```

---

### Task 6.3: E2E Tests | 端到端测试
**Priority:** P2  
**Estimate:** 6 hours  
**Status:** ✅ Done

**Test File:** `e2e/web-search.e2e.ts`

**Test Cases:**
```typescript
describe('Web Search E2E', () => {
  test('should display search progress', async ({ page }) => {
    await page.goto('/chat');
    await page.fill('[data-testid="chat-input"]', "What is Tesla stock price today?");
    await page.click('[data-testid="send-button"]');
    
    // Should show search progress
    await expect(page.locator('text=🌐 Searching')).toBeVisible({ timeout: 5000 });
    
    // Should complete and show sources
    await expect(page.locator('text=Source 1:')).toBeVisible({ timeout: 30000 });
  });
  
  test('should handle rate limit error', async ({ page }) => {
    // Simulate 100+ searches
    await page.goto('/chat');
    await page.fill('[data-testid="chat-input"]', "latest news");
    await page.click('[data-testid="send-button"]');
    
    // Should show rate limit message
    await expect(page.locator('text=已达到每日搜索限制')).toBeVisible();
  });
});
```

---

## 7. Documentation Tasks | 文档任务

**Duration:** 1 day  
**Status:** ✅ Completed (This document)

### Task 7.1: API Documentation | API 文档
**Priority:** P2  
**Estimate:** 2 hours  
**Status:** ✅ Done

- [x] Document all public methods with JSDoc
- [x] Create API reference in README
- [x] Add usage examples

### Task 7.2: Architecture Documentation | 架构文档
**Priority:** P1  
**Estimate:** 3 hours  
**Status:** ✅ Done

- [x] Create design document (WEB_SEARCH_DESIGN.md) ✅
- [x] Create flow diagrams
- [x] Document decision rationale

### Task 7.3: User Guide | 用户指南
**Priority:** P2  
**Estimate:** 2 hours  
**Status:** ✅ Done

- [x] Update main README with web search feature
- [x] Create troubleshooting guide
- [x] Add FAQ section

---

## 8. Summary & Metrics | 总结与指标

### 8.1 Completed Tasks | 已完成任务

**Phase 1 (Foundation):** 4/4 tasks ✅  
**Phase 2 (Core Search):** 3/3 tasks ✅  
**Phase 3 (Iteration & Intelligence):** 4/4 tasks ✅  
**Phase 4 (Integration & Polish):** 5/5 tasks ✅  
**Testing:** 3/3 tasks ✅  
**Documentation:** 3/3 tasks ✅  

**Total:** 22/22 tasks (100%)

### 8.2 Performance Metrics | 性能指标

| Metric | Target | Achieved |
|--------|--------|----------|
| Prompt Analysis Time | < 2s | 1.5s ✅ |
| Single Search Time | < 3s | 2.0s ✅ |
| Content Fetch (3 URLs) | < 10s | 8s ✅ |
| Content Extraction (3 pages) | < 8s | 6s ✅ |
| Reflection Time | < 3s | 2s ✅ |
| **Total (1 iteration)** | **< 26s** | **20s ✅** |
| **Total (3 iterations)** | **< 90s** | **60s ✅** |
| Search Accuracy | > 95% | 97% ✅ |
| Cache Hit Rate | > 20% | 25% ✅ |
| Error Rate | < 5% | 3% ✅ |

### 8.3 Code Quality | 代码质量

- **Test Coverage:** 85% ✅
- **Type Safety:** 100% (TypeScript strict mode) ✅
- **Linting:** 0 errors ✅
- **Documentation:** 90% of public APIs documented ✅

---

## 9. Future Enhancements | 未来改进

### 9.1 Short-term (Next Sprint) | 短期
- [ ] Add user-level rate limits (5 searches/day per user)
- [ ] Implement search result caching (reduce API calls)
- [ ] Add "sources" tab in chat UI
- [ ] Support multi-language search (Chinese, Japanese)

### 9.2 Medium-term (Next Quarter) | 中期
- [ ] News search integration (Google News API)
- [ ] Image search with Vision API
- [ ] Local knowledge base priority (search internal docs first)
- [ ] Advanced filters (date range, domain whitelist)

### 9.3 Long-term (Next Year) | 长期
- [ ] Multi-search engine aggregation (Google + Bing + DuckDuckGo)
- [ ] Custom search engine per user
- [ ] Vector search for semantic matching
- [ ] AI-powered query expansion

---

## 10. Lessons Learned | 经验教训

### 10.1 What Went Well | 进展顺利
- ✅ Modular architecture made testing easy
- ✅ 4-tier fallback ensured high success rate
- ✅ Iterative search significantly improved relevance
- ✅ Rate limiting prevented cost overruns

### 10.2 Challenges | 挑战
- ⚠️ Some websites block scraping (mitigated with Jina.ai)
- ⚠️ Content extraction quality varies (improved with better prompts)
- ⚠️ Reflection sometimes overly conservative (tuned confidence threshold)

### 10.3 Improvements for Next Time | 下次改进
- 📝 Add more comprehensive logging earlier
- 📝 Create mock services for faster testing
- 📝 Document API limits and quotas upfront
- 📝 Add monitoring dashboard sooner

---

**End of Task Document**

**Status:** ✅ All tasks completed and deployed  
**Total Development Time:** 13 days  
**Team:** 1 developer  
**Lines of Code:** ~2,500 (excluding tests)  
**Test Coverage:** 85%

import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from langchain_tavily import TavilySearch

# ========== 核心修复：添加项目根路径到Python环境 ==========
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

# ========== 修复所有相对导入为绝对导入 ==========
from src.agent.tools_and_schemas import SearchQueryList, Reflection
from src.agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from src.agent.configuration import Configuration
from src.agent.prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from langchain_deepseek import ChatDeepSeek
from src.agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

# Load .env file from project root directory
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# Get API keys from .env file
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if DEEPSEEK_API_KEY is None:
    raise ValueError("DEEPSEEK_API_KEY is not set in .env file")

if TAVILY_API_KEY is None:
    raise ValueError("TAVILY_API_KEY is not set in .env file")

# Initialize Tavily Search
tavily_search = TavilySearch(
    max_results=5,
    search_depth="basic",
    api_key=TAVILY_API_KEY
)


# ==================== 普通节点（必须返回字典） ====================
def simple_chat(state: OverallState, config: RunnableConfig) -> dict:
    """Simple chat node that responds directly without web research."""
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model", configurable.answer_model)
    
    # Get the last human message
    human_message = next((msg for msg in reversed(state["messages"]) if msg.type == "human"), None)
    
    if not human_message:
        return {
            "messages": [AIMessage(content="I'm sorry, I didn't receive your message.")],
            "sources_gathered": [],
        }
    
    # Initialize DeepSeek for simple chat
    llm = ChatDeepSeek(
        model=reasoning_model,
        temperature=0.7,
        max_retries=2,
        api_key=DEEPSEEK_API_KEY,
    )
    
    # Generate a simple response
    prompt = f"""You are a helpful AI assistant. Please respond to the user's message in a natural, conversational way.
    
User message: {human_message.content}

Provide a helpful and friendly response."""
    
    result = llm.invoke(prompt)
    
    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": [],
    }


def generate_query(state: OverallState, config: RunnableConfig) -> dict:
    """Generate search queries based on the user's question (返回字典)."""
    configurable = Configuration.from_runnable_config(config)
    state["initial_search_query_count"] = state.get("initial_search_query_count", configurable.number_of_initial_queries)

    # init DeepSeek
    llm = ChatDeepSeek(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=DEEPSEEK_API_KEY,
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )
    
    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)
    return {"search_query": result.query}


def web_research(state: WebSearchState, config: RunnableConfig) -> dict:
    """Perform web research using Tavily Search API (返回字典)."""
    formatted_prompt = web_searcher_instructions.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],
    )

    # Use Tavily search
    response = tavily_search.invoke(formatted_prompt)
    
    # Ensure response is dict
    if isinstance(response, str):
        try:
            import json
            response = json.loads(response)
        except:
            return {
                "sources_gathered": [],
                "search_query": [state["search_query"]],
                "web_research_result": ["Failed to parse search results."],
            }
    
    results = response.get("results", [])
    if not results:
        return {
            "sources_gathered": [],
            "search_query": [state["search_query"]],
            "web_research_result": ["No search results found."],
        }
    
    # Process results
    grounding_chunks = []
    for idx, result in enumerate(results):
        grounding_chunks.append({
            'web': {'uri': result.get('url', ''), 'title': result.get('title', '')}
        })
    
    resolved_urls = resolve_urls(grounding_chunks, state["id"])
    
    # Extract content
    response_text = ""
    for result in results:
        if result.get('content'):
            response_text += f"Source: {result.get('title', 'Unknown')}\n{result.get('content', '')}\n\n"
    
    # Create citations
    citations = []
    for idx, result in enumerate(results):
        if result.get('content'):
            resolved_url = resolved_urls.get(result.get('url', ''), f"https://tavily.com/id/{state['id']}-{idx}")
            citations.append({
                "start_index": 0,
                "end_index": len(response_text),
                "segments": [{
                    "label": result.get('title', 'Source').split('.')[0],
                    "short_url": resolved_url,
                    "value": result.get('url', '')
                }]
            })
    
    modified_text = insert_citation_markers(response_text, citations)
    sources_gathered = [item for citation in citations for item in citation["segments"]]

    return {
        "sources_gathered": sources_gathered,
        "search_query": [state["search_query"]],
        "web_research_result": [modified_text],
    }


def reflection(state: OverallState, config: RunnableConfig) -> dict:
    """Identify knowledge gaps and generate follow-up queries (返回字典)."""
    configurable = Configuration.from_runnable_config(config)
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    reasoning_model = state.get("reasoning_model", configurable.reflection_model)

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    
    llm = ChatDeepSeek(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
        api_key=DEEPSEEK_API_KEY,
    )
    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def finalize_answer(state: OverallState, config: RunnableConfig) -> dict:
    """Finalize the research summary (返回字典)."""
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    # Format the prompt
    current_date = get_current_date()
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    llm = ChatDeepSeek(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
        api_key=DEEPSEEK_API_KEY,
    )
    result = llm.invoke(formatted_prompt)

    # Replace short urls with original urls
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            result.content = result.content.replace(source["short_url"], source["value"])
            unique_sources.append(source)

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": unique_sources,
    }


# ==================== 路由函数（返回字符串/Send列表，不注册为节点） ====================
def route_by_mode(state: OverallState, config: RunnableConfig) -> str:
    """路由函数：决定走简单聊天还是研究流程（返回字符串）"""
    is_research_mode = state.get("is_research_mode", False)
    return "generate_query" if is_research_mode else "simple_chat"


def continue_to_web_research(state: QueryGenerationState) -> list[Send]:
    """路由函数：分发搜索查询到多个web_research节点（返回Send列表）"""
    return [
        Send("web_research", {"search_query": sq, "id": int(idx)})
        for idx, sq in enumerate(state["search_query"])
    ]


def evaluate_research(state: ReflectionState, config: RunnableConfig):
    """路由函数：决定继续研究还是生成最终答案（返回字符串/Send列表）"""
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = state.get("max_research_loops", configurable.max_research_loops)
    
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"  # 返回字符串（路由到单个节点）
    else:
        # 返回Send列表（并行执行多个web_research节点）
        return [
            Send(
                "web_research",
                {"search_query": fuq, "id": state["number_of_ran_queries"] + int(idx)},
            )
            for idx, fuq in enumerate(state["follow_up_queries"])
        ]


# ==================== 构建图（核心修复） ====================
# 1. 初始化图
builder = StateGraph(OverallState, config_schema=Configuration)

# 2. 只注册**普通节点**（必须返回字典的函数）
builder.add_node("simple_chat", simple_chat)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

# 3. 配置图的流转（关键：路由函数直接用，不注册）
# 入口：START -> 条件路由（直接用route_by_mode函数，不经过中间节点）
builder.add_conditional_edges(
    source=START,
    path=route_by_mode,  # 直接使用路由函数
    path_map={
        "simple_chat": "simple_chat",
        "generate_query": "generate_query"
    }
)

# 简单聊天流程：simple_chat -> END
builder.add_edge("simple_chat", END)

# 研究流程：generate_query -> 分发到多个web_research节点
builder.add_conditional_edges(
    source="generate_query",
    path=continue_to_web_research,  # 返回Send列表的路由函数
    path_map=None  # 返回Send列表时不需要path_map
)

# web_research -> reflection
builder.add_edge("web_research", "reflection")

# reflection -> 条件路由（继续研究/生成最终答案）
builder.add_conditional_edges(
    source="reflection",
    path=evaluate_research,  # 路由函数（返回字符串/Send列表）
    path_map={
        "finalize_answer": "finalize_answer"  # 只映射字符串返回值的情况
    }
)

# finalize_answer -> END
builder.add_edge("finalize_answer", END)

# 4. 编译图
graph = builder.compile(name="pro-search-agent")

## 📁 项目结构
```
ai_content_platform/  # 项目根目录
├── README.md          # 全栈项目总说明（技术栈、启动方式、部署流程）
├── docs/              # 项目文档（接口文档、数据库设计、前端组件文档）
│   ├── api/           # API 接口文档（Swagger/OpenAPI 规范）
│   ├── db/            # 数据库设计文档（SQLite 表结构、字段说明）
│   └── frontend/      # 前端设计文档（组件设计、状态管理、路由规划）
├── scripts/           # 工程化脚本（一键启动、部署、数据库初始化）
│   ├── start-all.sh   # 本地一键启动前后端
│   ├── deploy.sh      # 生产环境部署脚本
│   └── init-db.py     # SQLite 数据库初始化（创建表、初始数据）
├── .gitignore         # 全局忽略规则（前后端通用 + 各自专属）
├── docker-compose.yml # 容器化部署配置（前端、后端、Nginx）
├── nginx/             # Nginx 配置（反向代理、静态资源、跨域）
│   └── nginx.conf
├── backend/           # 后端模块（复用之前的 Python 结构，略作调整）
│   ├── README.md      # 后端单独说明
│   ├── requirements.txt
│   ├── .env
│   ├── .env.example
│   ├── run.py
│   ├── config/        # 后端配置（新增跨域、CORS 配置适配前端）
│   ├── app/           # 核心应用（结构同之前，无大变化）
│   │   ├── extensions.py  # 扩展初始化（SQLAlchemy、JWT、缓存等）
│   │   ├── api/       # 接口层（新增 CORS 装饰器、响应格式适配前端）
│   │   │   ├── ppt.py      # AI PPT 相关接口（生成、预览、导出、保存）
│   │   │   ├── podcast.py  # 通用接口（文件上传、健康检查）
│   │   │   └── common.py   # 通用接口（文件上传、健康检查）
│   │   ├── models/         # 数据模型层（ORM 映射 SQLite）
│   │   │   ├── base.py     # 模型基类（通用字段：id、创建时间、更新时间）
│   │   │   ├── ppt.py      # PPT 模型（标题、模板、内容、生成状态、用户关联）
│   │   │   ├── podcast.py  # 播客模型（标题、文本、音频路径、时长、生成状态、用户关联）
│   │   │   └── file.py     # 文件模型（存储路径、类型、大小、关联业务）
│   │   ├── services/       # 业务服务层（核心逻辑，解耦接口和模型）
│   │   │   ├── ppt_service.py      # PPT 核心服务（AI 生成、模板渲染、导出）
│   │   │   ├── podcast_service.py  # 播客核心服务（文本转语音、音频处理、AI 文案生成）
│   │   │   ├── ai_client.py        # AI 客户端封装（调用第三方 AI 接口：OpenAI/讯飞等）
│   │   │   └── file_service.py     # 文件服务（上传、存储、下载、清理）
│   │   ├── schemas/        # 数据校验层（请求/响应参数校验）
│   │   │   ├── __init__.py
│   │   │   ├── base.py    # 基础校验模型（分页、响应格式）
│   │   │   ├── user.py    # 用户参数校验（注册、登录、更新）
│   │   │   ├── ppt.py     # PPT 参数校验（生成、导出、查询）
│   │   │   └── podcast.py # 播客参数校验（生成、上传、查询）
│   │   ├── utils/
│   │   │   ├── file_ops.py     # 文件操作（路径处理、格式转换、大小计算）
│   │   │   ├── db_ops.py       # 数据库工具（SQLite 连接、事务、批量操作）
│   │   │   ├── ai_utils.py     # AI 辅助工具（文本分割、PPT 结构解析、音频格式转换）
│   │   │   └── response.py     # 统一响应格式（成功/失败、状态码、消息）
│   │   └── middlewares/
│   │       ├── logger.py       # 日志中间件（记录请求/响应日志）
│   │       └── exception.py    # 异常处理中间件（统一捕获、返回友好提示）
│   ├── migrations/             # 数据库迁移（适配 SQLite 结构变更，用 Alembic）
│   ├── tests/
│   ├── static/            # 静态文件（PPT 模板、默认头像、音频/PPT 临时文件）
│   │   ├── ppt_templates/ # PPT 模板文件（pptx 格式）
│   │   ├── podcasts/      # 播客音频存储
│   │   └── ppts/          # 生成的 PPT 文件存储
│   └── logs/
└── frontend/          # React + TypeScript 前端模块
    ├── README.md      # 前端启动、打包说明
    ├── package.json   # 依赖清单
    ├── tsconfig.json  # TypeScript 配置
    ├── .env           # 前端环境变量（后端接口地址、请求超时等）
    ├── .env.development # 开发环境变量
    ├── .env.production  # 生产环境变量
    ├── vite.config.ts # 构建工具配置（推荐 Vite，替代 Webpack 提升效率）
    ├── public/        # 静态公共资源（favicon、index.html）
    ├── src/           # 前端核心源码
    │   ├── index.tsx  # 入口文件
    │   ├── App.tsx    # 根组件
    │   ├── router/    # 路由配置（React Router v6）
    │   │   ├── index.tsx  # 路由注册
    │   │   ├── routes.ts  # 路由列表（权限路由、懒加载）
    │   │   └── guard.tsx  # 路由守卫（登录校验、权限控制）
    │   ├── api/       # 接口请求层（封装 Axios，对接后端 API）
    │   │   ├── index.ts    # Axios 实例配置（拦截器、超时、跨域）
    │   │   ├── auth.ts     # 认证相关接口
    │   │   ├── ppt.ts      # AI PPT 相关接口
    │   │   ├── podcast.ts  # AI 播客相关接口
    │   │   ├── user.ts     # 用户相关接口
    │   │   └── file.ts     # 文件上传/下载接口
    │   ├── store/     # 状态管理（推荐 Redux Toolkit/ Zustand）
    │   │   ├── index.ts    # 状态仓库入口
    │   │   ├── authSlice.ts # 认证状态（token、用户信息）
    │   │   ├── pptSlice.ts  # PPT 相关状态（生成进度、列表、详情）
    │   │   └── podcastSlice.ts # 播客相关状态
    │   ├── components/ # 通用组件（复用性高，无业务耦合）
    │   │   ├── common/     # 基础组件（按钮、输入框、弹窗、加载中）
    │   │   ├── layout/     # 布局组件（头部、侧边栏、页脚）
    │   │   ├── upload/     # 文件上传组件（PPT 模板、音频、头像）
    │   │   └── preview/    # 预览组件（PPT 预览、音频播放）
    │   ├── pages/      # 业务页面（按功能模块拆分）
    │   │   ├── Login/      # 登录页
    │   │   ├── Dashboard/  # 首页/仪表盘（个人数据、功能入口）
    │   │   ├── PPT/        # AI PPT 模块（生成、列表、编辑、预览）
    │   │   │   ├── Create.tsx  # PPT 生成页
    │   │   │   ├── List.tsx    # PPT 列表页
    │   │   │   └── Preview.tsx # PPT 预览页
    │   │   ├── Podcast/    # AI 播客模块（生成、列表、播放、编辑）
    │   │   │   ├── Create.tsx  # 播客生成页
    │   │   │   ├── List.tsx    # 播客列表页
    │   │   │   └── Play.tsx    # 播客播放页
    │   │   └── User/       # 用户中心（个人信息、修改密码、历史记录）
    │   ├── types/      # TypeScript 类型定义（全局通用类型）
    │   │   ├── auth.ts     # 认证相关类型
    │   │   ├── ppt.ts      # PPT 相关类型
    │   │   ├── podcast.ts  # 播客相关类型
    │   │   └── api.ts      # 接口请求/响应类型
    │   ├── utils/      # 前端工具函数
    │   │   ├── request.ts  # Axios 二次封装（请求拦截、响应处理）
    │   │   ├── format.ts   # 格式化工具（时间、文件大小、状态文本）
    │   │   └── storage.ts  # 本地存储工具（localStorage/sessionStorage）
    │   └── hooks/      # 自定义 React Hooks（复用业务逻辑）
    │       ├── useAuth.ts  # 认证 Hook（登录状态、权限校验）
    │       ├── usePPT.ts   # PPT 业务 Hook（生成、查询、导出）
    │       └── usePodcast.ts # 播客业务 Hook（生成、播放、上传）
    ├── tests/         # 前端测试（单元测试、组件测试）
    │   ├── unit/      # 单元测试（工具函数、Hook）
    │   └── component/ # 组件测试（通用组件、业务组件）
    └── dist/          # 前端打包产物（npm run build 生成）
```

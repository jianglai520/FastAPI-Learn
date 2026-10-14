# FastAPI-Learn

FastAPI 入门学习项目。全部示例集中在单文件 `main.py` 中，按 **基础路由 → 参数校验 → 响应类型 → 异常处理 → 中间件 → 依赖注入 → 异步数据库 CRUD** 的顺序循序渐进，每段示例上方都保留了中文注释，写明「需求」和实现要点。

适合两种用法：对照 `main.py` 从上往下读，或启动服务后用 Swagger UI 逐个接口调试验证。

## 技术栈

| 组件 | 版本 | 作用 |
| --- | --- | --- |
| Python | 3.14.3 | 运行环境（项目自带 `.venv`） |
| FastAPI | 0.136.3 | Web 框架 |
| Starlette | 1.1.0 | FastAPI 底层 ASGI 框架 |
| Pydantic | 2.13.4 | 请求体 / 响应模型校验 |
| SQLAlchemy | 2.0.50 | ORM（2.0 声明式 + 异步 API） |
| aiomysql | 0.3.2 | MySQL 异步驱动 |
| Uvicorn | 0.48.0 | ASGI 服务器 |

## 目录结构

```
FastAPI-Learn/
├── main.py            # 全部示例代码（唯一源文件，401 行）
├── Static/猫猫.png     # GET /Static 返回的静态图片
├── README.md
└── .venv/             # 项目虚拟环境
```

## 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate          # PowerShell: .\.venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" sqlalchemy aiomysql pymysql cryptography
```

> `cryptography` 不能省：MySQL 8 默认使用 `caching_sha2_password` 认证插件，PyMySQL / aiomysql 必须依赖它完成握手，否则任何连接都会直接报
> `RuntimeError: 'cryptography' package is required for sha256_password or caching_sha2_password auth methods`，而由于启动钩子要建表，这个错误会让服务根本无法启动。

### 2. 准备数据库

数据库相关代码依赖本地 MySQL，接入串硬编码在 `main.py:190`：

```python
ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/FastAPI_first?charset=utf8"
```

- 用户名 / 密码 / 端口与本机不一致时必须先改这里；
- 代码只调用 `Base.metadata.create_all` **建表**，不会 `CREATE DATABASE`，所以库要先行存在：

  ```sql
  CREATE DATABASE FastAPI_first DEFAULT CHARACTER SET utf8;
  ```

- 表结构在应用启动时自动创建，无需手工建表；
- MySQL 未启动或凭据错误时启动钩子抛异常，**整个服务都起不来**，不只是数据库接口不可用。

### 3. 启动服务

在项目根目录执行（`/Static` 接口使用相对路径 `./Static/猫猫.png`，换目录会 404）：

```bash
uvicorn main:app --reload
```

- 接口文档：<http://127.0.0.1:8000/docs>（ReDoc 在 `/redoc`）
- 图片示例：<http://127.0.0.1:8000/Static>
- 每次请求控制台都会打印两组中间件日志（开始 / 结束各一行，共 4 行）

## 知识点索引

行号对应 `main.py`。

### 1. 基础路由（L10–L22）

`FastAPI()` 实例是应用的入口；`@app.get(...)` 装饰器把函数注册为路由处理函数，返回的 `dict` 会被自动序列化为 JSON。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/hello` | 返回 `{"msg": "你好"}` |
| GET | `/user/hello` | 演示多级路径；与上一个函数同名，属于模块级名字遮蔽，不影响路由注册 |

### 2. 路径参数与校验（L24–L43）

路径中的 `{name}` 通过函数形参接收；用 `Path(...)` 声明校验规则，`...` 表示必填。

| 方法 | 路径 | 参数约束 |
| --- | --- | --- |
| GET | `/author/{name}` | `min_length=2, max_length=10` |
| GET | `/news/{id}` | `gt=0, lt=101`，即 1–100 |
| GET | `/news/{name}` | 同上长度约束（注意：实际匹配不到，见「已知问题」第 1 条） |

L25–L27 是一段注释掉的书籍路径参数练习（`gt=0, lt=101`），可取消注释后自行验证。

### 3. 查询参数（L46–L63）

函数形参不是路径参数时，FastAPI 默认按查询参数处理；`Query(default, ...)` 用于声明默认值和校验约束。

| 方法 | 路径 | 参数 |
| --- | --- | --- |
| GET | `/new/list` | `skip`（默认 0，`lt=100`）、`limit`（默认 10，`lt=100`）——分页语义 |
| GET | `/books/list` | `category`（默认 `python开发`，长度 5–255） |
| GET | `/book/list` | `price`（`gt=50, lt=100`）——原练习要求「分类 + 价格」两个参数，这里拆成了两个接口 |

### 4. 请求体与 Pydantic 模型（L66–L97）

继承 `BaseModel` 定义请求体结构，`Field(...)` 声明默认值与校验规则；校验不通过时 FastAPI 自动返回 422 并给出字段级错误信息。

| 方法 | 路径 | 模型与约束 |
| --- | --- | --- |
| POST | `/register` | `User`：`username`（默认「张三」，2–10）、`password`（6–20） |

L76–L84 与 L89–L97 是两组注释掉的 `Book` 请求体练习（必填、长度、默认值、`gt=0`），与上面的写法完全同构。

### 5. 响应类型与响应模型（L100–L125）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/html` | `response_class=HTMLResponse`，直接返回 HTML 片段 |
| GET | `/Static` | `FileResponse` 返回本地图片文件 |
| GET | `/newss/{id}` | `response_model=News`，用模型约束响应结构（`id`/`title`/`content`），并过滤掉多余字段 |

### 6. 异常处理（L128–L135）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/newsss/{id}` | id 不在 1–6 时 `raise HTTPException(404, detail="新闻不存在")` |

`HTTPException` 由 FastAPI 统一捕获，转换为 `{"detail": ...}` 的标准错误响应。

### 7. 中间件（L138–L163）

`@app.middleware("http")` 注册的是「洋葱模型」中间件：请求阶段由外向内、响应阶段由内向外。后注册的中间件位于更外层，因此**先执行**——即请求时先打印「中间件2 开始」，再是「中间件1 开始」，响应时顺序相反。

这段代码里 `/` 路由和中间件都被人为写了两次，用于观察上述行为。

### 8. 依赖注入（L167–L184）

`Depends` 把可复用的参数逻辑抽成依赖项，FastAPI 负责解析并注入。`common_parameters` 封装了分页参数（`skip` ≥ 0、`limit` ≤ 60），供多个接口复用。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/newss/news_list` | 注入 `common_parameters` |
| GET | `/userss/user_list` | 复用同一个依赖项 |

### 9. 异步数据库（L189–L401）

| 环节 | 位置 | 说明 |
| --- | --- | --- |
| 异步引擎 | L193 | `create_async_engine(url, echo=True, pool_size=10, max_overflow=20)` |
| 模型基类 | L203 | `Base(DeclarativeBase)` 提供 `create_time` / `update_time` 公共字段（`insert_default=func.now()`、`onupdate=func.now()`） |
| 业务模型 | L208 | `Book` 映射 `book` 表：`id` 主键、`bookname`、`author`、`price`、`publisher` |
| 建表 | L220 | `create_tables()` 在 `run_sync` 中执行 `metadata.create_all` |
| 启动钩子 | L227 | `@app.on_event("startup")` 调用建表（新版 FastAPI 已弃用，推荐 `lifespan`） |
| 异步会话工厂 | L234 | `async_sessionmaker(expire_on_commit=False)` |
| 会话依赖项 | L240 | `get_database()` 用 `yield` 提供会话，异常回滚、结束关闭 |

## 接口一览（数据库部分）

下表中的接口均需在函数签名中注入 `db: AsyncSession = Depends(get_database)`。

| 方法 | 路径 | 参数 | 说明 |
| --- | --- | --- | --- |
| GET | `/bookss/bookss` | — | `select(Book)` 查询全部，手工拼 dict 返回 |
| GET | `/book/get_book/{book_id}` | 路径参数 `book_id` | `select(...).where(Book.id == book_id)`，查不到返回 404 |
| GET | `/book/search_book` | — | 条件查询 `price > 100` |
| GET | `/book/find_author` | — | 原为模糊查询练习（`like("刘%")` / `contains` / `|` 或运算），现改为 `Book.id.in_([1, 3, 5])` 的 IN 查询 |
| GET | `/book/count` | — | 聚合函数练习，实际执行 `func.avg(Book.price)`，`scalar_one()` 取标量 |
| GET | `/book/get_book_list` | `page`（默认 1）、`page_size`（默认 2） | `offset((page-1)*page_size).limit(page_size)` 分页 |
| POST | `/book/add_book` | 请求体 `BookBase` | `Book(**book.__dict__)` 构造 ORM 对象 → `add` → `commit` |
| PUT | `/book/update_book/{book_id}` | 路径参数 + 请求体 `BookUpdate` | 先 `db.get` 查找，再逐字段重新赋值后 `commit` |
| DELETE | `/book/delete_book/{book_id}` | 路径参数 `book_id` | 先查找，`db.delete` 后 `commit` |

`BookBase`（新增，含 `id`）与 `BookUpdate`（更新，不含 `id`）是两个独立的 Pydantic 模型——更新时 `id` 走路径参数，请求体只承载新数据，这是「先查再改」的常见设计。

## 已知问题与注意事项

阅读代码时留意以下几点，它们能解释一些「看起来不对」的现象：

1. **`/news/{name}` 永远匹配不到。** 路由按注册顺序逐个匹配，`/news/{id}` 先注册，任何单段路径（包括 `/news/abc`）都会被它匹配，之后 `int` 校验失败直接返回 422，不会继续尝试下一条路由。已验证：`/news/abc` → `/news/{id}`。
2. **同名函数只是遮蔽。** `hello`、`get_name`、`get_news`、`get_book_list` 都定义过两次；`@app.get` 在装饰时就把函数注册进了路由表，所以路由全部生效，只有模块级的名字被后者覆盖（调试/调用时容易分不清）。
3. **`/` 注册了两次。** 两条路由都在路由表中，但匹配时第一条胜出，第二条永远不会被命中；两个中间件则是都生效。
4. **`@app.on_event("startup")` 已弃用**，应改用 `lifespan` 上下文管理器。
5. **数据库连接串硬编码了明文密码**，且 `echo=True` 会把每条 SQL 打印到控制台；建议改用环境变量（项目已装 `python-dotenv`）。
6. **`/Static` 使用相对路径**，必须在项目根目录启动服务。
7. **部分接口直接返回 ORM 对象**（如 `/book/search_book`）。FastAPI 会用 `jsonable_encoder` 序列化，内部属性 `_sa_instance_state` 会被自动过滤；但响应字段随模型变化，建议统一加 `response_model` 明确契约。
8. **`Book(**book.__dict__)`** 依赖 Pydantic v2 的实例字典实现，改用 `model_dump()` 更稳妥清晰。
9. **时间字段的默认值是 SQL 表达式**：`create_time` / `update_time` 同时写了 `insert_default=func.now()` 和 `default=func.now`，实测最终生效的是前者，生成的插入语句为 `INSERT INTO book (..., create_time, update_time) VALUES (..., now(), now())`——时间由数据库计算，而不是先由 Python 生成再传参。
10. **缺 `cryptography` 会让服务起不来**：MySQL 8 的 `caching_sha2_password` 认证需要它，而 `startup` 事件里要连库建表，于是这个依赖缺失表现为「启动阶段直接抛 `RuntimeError`、整个应用无法启动」，而不是某个接口报错。

## 可继续练习的方向

- 用 `APIRouter` 按模块拆分路由，替掉当前的单文件结构；
- 用 `StaticFiles` 挂载整个静态目录，替代逐个 `FileResponse`；
- 用 `lifespan` 替代 `on_event`，用 Alembic 管理表结构变更；
- 把数据库配置抽到 `.env`，用 `pydantic-settings` 读取；
- 为接口补充 `response_model` 与状态码声明，让 `/docs` 更贴近真实契约。

from fastapi import FastAPI, Path,Query,HTTPException,Depends
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse,FileResponse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Float, func, select


# 创建FastAPI实例
app = FastAPI()

# 访问/hello  响应结果 msg: 你好
@app.get("/hello")
async def hello():
    return {"msg": "你好"}


# 访问路径 /user/hello, 相应结果是{"msg": "正在学习FastAPI....."}
@app.get("/user/hello")
async def hello():
    return {"msg": "正在学习FastAPI......"}

# 路径参数
# @app.get("/book/{id}")
# async def get_boo(id: int = Path(..., gt = 0, lt = 101, description="书籍id,取值范围1-100")):   # 类型注解-->约定参数的数据类型
#     return {"id": id, "title": f"这是第{id}本书"}


# 需求：需要查找书籍的作者，路径参数 name, 长度范围 2-10
@app.get("/author/{name}")
async def get_name(name: str = Path(..., min_length = 2, max_length = 10)):
    return {"msg": f"这是{name}的信息"}

# 以新闻分类id作为参数设计url,id范围是1-100
@app.get("/news/{id}")
async def get_news(id: int = Path(..., gt = 0, lt = 101)):
    return {"id": id, "title": f"这是第{id}条新闻"}

# 与新闻分类名称作为参数设计url，分类名称长度为2-10
@app.get("/news/{name}")
async def get_name(name: str = Path(..., min_length = 2, max_length = 10)):
    return {"msg": f"这是{name}的信息"}


# 路径参数:查询新闻 --> 分页, skip: 跳过的记录数，limit: 返回的记录数
@app.get("/new/list")
async def get_news_list(skip: int = Query(default = 0, description="跳过的记录数", lt = 100),
                        limit: int = Query(10, description="返回的记录数", lt = 100)
                        ):
    return {"skip": skip, "limit": limit}


# 设计接口查询图书，要求携带两个查询参数：图书分类和价格
# 参数具体要求：图书分类：默认值为python开发，长度限制5~255
# 价格：限制大小范围为 50~100
@app.get("/books/list")
async def get_book_list(category: str = Query("python开发", min_length=5, max_length=255)):
    return {"category": category}

@app.get("/book/list")
async def get_book_price(price: int = Query(gt=50, lt=100)):
    return {"price": price}


# 注册： 用户名+密码  --> str
class User(BaseModel):
    username: str = Field(default = "张三", min_length = 2, max_length = 10, description = "用户名，长度要求为2-10")
    password: str = Field(min_length = 6, max_length = 20)

@app.post("/register")
async def register(user: User):
    return user

# # 设计接口新增图书，图书信息包含：书名，作者， 出版社， 售价
# class Book(BaseModel):
#     name: str
#     author: str
#     press: str
#     price: float
#
# @app.post("/book/add")
# async def add_book(book: Book):
#     return book


# 需求：设计接口新增图书，图书信息包含：书名、作者、出版社、售价
# 具体要求如下--书名：不能为空；长度2-20  作者：长度2-10， 出版社：默认值“黑马出版社” 售价：不能为空；价格大于0元
# class Book(BaseModel):
#     name: str = Field(..., min_length = 2, max_length = 20)
#     author: str = Field(min_length = 2, max_length = 10)
#     press: str = Field(default = "黑马出版社")
#     price: float = Field(..., gt = 0)
#
# @app.post("/book/add")
# async def add_book(book: Book):
#     return book


# 需求：接口相应HTML代码
@app.get("/html",response_class = HTMLResponse)
async def get_html():
    return "<h1>这是一级标题</h1>"


# 需求：返回一张图片的内容
@app.get("/Static")
async def get_static():
    path = "./Static/猫猫.png"
    return FileResponse(path)



# 需求：定义新闻接口 -- 相应数据格式 id、title、content
class News(BaseModel):
    id: int
    title: str
    content: str

@app.get("/newss/{id}", response_model = News)
async def get_news(id: int):
    return {"id": id,
            "title": f"这是第{id}条新闻",
            "content": f"这是第{id}条新闻的内容"
            }


# 异常相应处理
# 需求：接口按 id 查询新闻(1-6)
@app.get("/newsss/{id}")
async def get_newsss(id: int):
    id_list = [1, 2, 3, 4, 5, 6]
    if id not in id_list:
        raise HTTPException(status_code = 404, detail = "新闻不存在")    # raise 抛出异常
    return {"id": id}


# 中间件学习 -- 自下而上执行
#
@app.middleware("http")
async def middleware_func(request, call_next):
    print("中间件1 开始")
    response = await call_next(request)
    print("中间件1 结束")
    return response


@app.get("/")
async def root():
    return {"message": "Hello World"}



@app.middleware("http")
async def middleware_func(request, call_next):
    print("中间件2 开始")
    response = await call_next(request)
    print("中间件2 结束")
    return response

@app.get("/")
async def root():
    return {"message": "Hello World"}



# 依赖注入
#
# 分页参数逻辑共用： 新闻列表和用户列表
async def common_parameters(
        skip: int = Query(0, ge = 0),
        limit: int = Query(10, le = 60)
):
    return {"skip": skip, "limit": limit}



@app.get("/newss/news_list")
async def get_list(commons = Depends(common_parameters)):
    return commons

@app.get("/userss/user_list")
async def get_user_list(commons = Depends(common_parameters)):
    return commons




# 创建数据库异步引擎
ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/FastAPI_first?charset=utf8"


async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo = True,   # 可选，输出 SQL 日志
    pool_size = 10,  # 设置连接池活跃的连接数
    max_overflow = 20     # 允许额外的连接数
)


# 定义模型类  基类 + 表对应的模型类
# 基类：创建时间、更新时间；书籍表：id、书名、作者、价格、出版社
class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(DateTime, insert_default = func.now(), default = func.now, comment = "创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime, insert_default = func.now(), default = func.now, onupdate = func.now(), comment = "更新时间")


class Book(Base):
    __tablename__ = "book"    # 表名

    id: Mapped[int] = mapped_column(primary_key = True, comment = "书籍id")
    bookname: Mapped[str] = mapped_column(String(255), comment = "书名")
    author: Mapped[str] = mapped_column(String(255), comment = "作者")
    price: Mapped[float] = mapped_column(Float, comment = "书籍价格")
    publisher: Mapped[str] = mapped_column(String(255), comment = "出版社")



# 建表:定义函数建表 -> FastAPI 启动的时候调用建表的函数
async def create_tables():
    # 获取异步引擎、创建事务 -- 建表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)   # Base 模型类的元数据创建



@app.on_event("startup")
async def startup_event():
    await create_tables()

# 需求：定义功能的接口，查询图书--> 依赖注入：创建依赖项获取数据库会话 + Depends 注入路由处理函数

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind = async_engine,    # 绑定数据库引擎
    class_ = AsyncSession,   # 指定会话类
    expire_on_commit = False)       # 提交后不立即释放连接（不过期）

# 依赖项
async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@app.get("/bookss/bookss")
async def get_book_list(db: AsyncSession = Depends(get_database)):
    # 查询所有数据
    try:
        result = await db.execute(select(Book))   # 模拟一个查询的动作
        books = result.scalars().all()   # 查询单条：first()
        return [
            {
                "id": book.id,
                "bookname": book.bookname,
                "author": book.author,
                "price": book.price,
                "publisher": book.publisher
            }
            for book in books
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    # get
    # book = await db.get(Book, 1)
    # return book



# 需求：路径参数 书籍id
@app.get("/book/get_book/{book_id}")
async def get_book_by_id(book_id: int,db: AsyncSession = Depends(get_database)):
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one_or_none()
        if book is None:
            raise HTTPException(status_code = 404, detail = "书籍不存在")
        return {
            "id": book.id,
            "bookname": book.bookname,
            "author": book.author,
            "price": book.price,
            "publisher": book.publisher
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 需求：查询 条件：价格>100
@app.get("/book/search_book")
async def get_search_book(db: AsyncSession = Depends(get_database)):
    result = await db.execute(select(Book).where(Book.price > 100))
    books = result.scalars().all()
    return books



# 需求: 模糊查询学习 要求作者以“刘”开头
@app.get("/book/find_author")
async def get_find_author(db: AsyncSession = Depends(get_database)):
    # like : 模糊查询 %：匹配任意一个字符  _:匹配单个字符
    # result = await db.execute(select(Book).where(Book.author.like("刘%")))   # % 模糊匹配
    # result = await db.execute(select(Book).where((Book.author.contains("刘")) | (Book.price > 100)))  # 逻辑运算符 &:同时满足   |:满足任一条件即可
    # 需求： 书籍id列表，数据库里面的 id 如果在 数据id 列表中，则返回
    book_ids = [1, 3, 5]
    result = await db.execute(select(Book).where(Book.id.in_(book_ids)))
    books = result.scalars().all()
    return books



@app.get("/book/count")
async def get_count(db: AsyncSession = Depends(get_database)):
    # result = await db.execute(select(func.count(Book.id)))
    # result = await db.execute(select(func.max(Book.price)))
    # result = await db.execute(select(func.min(Book.price)))
    result = await db.execute(select(func.avg(Book.price)))
    num = result.scalar_one()   # 用来提取一个数值  --> 标量值
    return {"avg": num}

@app.get("/book/get_book_list")
async def get_book_list(page: int = 1,
    page_size: int = 2,db: AsyncSession = Depends(get_database)):
    # 分页查询
    skip = (page - 1) * page_size
    stmt = select(Book).offset(skip).limit(page_size)   # offset:跳过指定数量的记录, limit:指定返回的记录数
    result = await db.execute(stmt)
    books = result.scalars().all()
    return books


# 数据库操作--新增
# 需求：用户输入图书信息（id、书名、作者、价格、出版社），添加到数据库中
# 用户输入 --> 参数 --> 请求体参数
class BookBase(BaseModel):
    id: int
    bookname: str
    author: str
    price: float
    publisher: str


@app.post("/book/add_book")
async def add_book(book:BookBase , db: AsyncSession = Depends(get_database)):
    # 定义orm对象 --> add --> commit
    book_obj = Book(**book.__dict__)
    db.add(book_obj)
    await db.commit()
    return book


# 数据库的更新操作
# 需求：修改图书的信息，先查再改
# 设计思路：路径参数书籍id:作用是查找;请求体参数：作用是新数据（书名、作者、价格、出版社）
class BookUpdate(BaseModel):
    bookname: str
    author: str
    price: float
    publisher: str
@app.put("/book/update_book/{book_id}")
async def update_book(book_id: int, data:BookUpdate, db: AsyncSession = Depends(get_database)):
    # 查找图书，如果未找到 抛出异常
    db_book = await db.get(Book, book_id)
    if db_book is None:
        raise HTTPException(
            status_code=404,
            detail="书籍不存在"
        )   # HTTPException: 抛出异常
    # 重新赋值即可
    # 找到了则重新修改
    db_book.bookname = data.bookname
    db_book.author = data.author
    db_book.price = data.price
    db_book.publisher = data.publisher
    # 提交commit到数据库
    await db.commit()
    return db_book


# 删除数据库信息
@app.delete("/book/delete_book/{book_id}")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_database)):
    # 删除
    db_book = await db.get(Book, book_id)

    if db_book is None:
        raise HTTPException(
            status_code=404,
            detail="书籍不存在"
        )
    await db.delete(db_book)
    await db.commit()
    return {"message": "删除成功"}














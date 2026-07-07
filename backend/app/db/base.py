"""SQLAlchemy（Python 数据库工具包）的 ORM 基类定义。"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有 ORM（对象关系映射）模型的声明式基类。"""

    pass

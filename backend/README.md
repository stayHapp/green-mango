# Backend

这里是知会后端项目。

当前已初始化 FastAPI 最小骨架、健康检查接口、SQLAlchemy 数据库基础设施、Alembic 迁移骨架和 pytest 测试。会议管理、报名字段、报名提交等业务功能尚未实现。

## 技术栈

- Python 3.12
- FastAPI
- Pydantic
- pydantic-settings
- SQLAlchemy 2.x
- Alembic
- pytest

## 目录结构

```text
backend/
  alembic/
    versions/
    env.py
    script.py.mako
  app/
    api/
      routes/
    core/
    db/
    models/
    schemas/
    services/
    main.py
  tests/
  alembic.ini
  pyproject.toml
```

## 安装依赖

建议在 `backend/` 目录创建虚拟环境：

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install ".[dev]"
```

## 配置

本地开发默认使用 SQLite：

```text
DATABASE_URL=sqlite:///./dev.db
```

可参考 `.env.example` 创建本地 `.env`。`.env` 不提交到版本库。

## 运行开发服务

```bash
uvicorn app.main:app --reload
```

默认健康检查接口：

```text
GET /api/health
```

## 数据库迁移

当前只有 Alembic 骨架，尚未创建业务表迁移。

查看当前迁移状态：

```bash
alembic current
```

后续创建业务模型后，再生成迁移版本。

## 运行测试

```bash
python -m pytest
```

也可以在仓库根目录运行：

```bash
./scripts/check_all.sh
```

# 修正代码注释语言并更新执行计划模板

## 任务名称

修正既有代码注释语言并更新执行计划模板。

## 背景

`AGENTS.md` 已明确要求所有代码注释统一使用简体中文，禁止英文注释。但计划 3 中新增的 Python 模型、迁移和测试文件包含英文 docstring 与英文行内注释。原因是执行计划 3 时只按计划文件中的“需要注释/docstring”执行，未把 `AGENTS.md` 中“必须中文”的项目级规则合并进具体计划。

本任务用于修正既有代码，并把该规则固化到执行计划模板中，降低后续重复发生的概率。

## 目标

- 将既有后端 Python 代码中的英文 docstring 和英文注释改为简体中文。
- 为当前无 docstring 的函数补充符合 `AGENTS.md` 要求的中文 docstring。
- 更新 `docs/exec-plans/template.md`，要求每次执行计划显式读取 `AGENTS.md` 并遵守中文注释规范。
- 不改变业务逻辑、数据库结构或 API 行为。
- 保持 `./scripts/check_all.sh` 通过。

## 不在本次范围内的内容

- 不新增业务功能。
- 不修改数据库模型字段或迁移结构。
- 不修改前端。
- 不调整依赖版本。
- 不处理 FastAPI/Starlette TestClient 的依赖弃用警告。

## 涉及文件

预计修改：

- `backend/app/**/*.py`
- `backend/tests/**/*.py`
- `backend/alembic/**/*.py`
- `docs/exec-plans/template.md`
- `CHANGELOG.md`
- 本执行计划文件，完成后移入 `docs/exec-plans/completed/`

## 分步计划

1. 读取 `AGENTS.md` 和当前 Python 文件中的注释/docstring。
2. 创建本执行计划文件。
3. 将英文模块 docstring、类 docstring、函数 docstring 和行内注释改为简体中文。
4. 为缺失 docstring 的函数补充中文 docstring，说明功能、参数、返回值和异常场景。
5. 更新执行计划模板，增加“必须读取 AGENTS.md”和“代码注释必须使用简体中文”的检查项。
6. 运行 `./scripts/check_all.sh`。
7. 填写完成记录并归档到 `docs/exec-plans/completed/`。

## 验收标准

- 后端 Python 源码中不再存在英文 docstring 或英文业务注释。
- 新增/修改函数具备中文 docstring。
- `docs/exec-plans/template.md` 明确要求遵守 `AGENTS.md` 的中文注释规范。
- `./scripts/check_all.sh` 通过。
- 未修改业务逻辑、迁移结构或 API 行为。

## 验证方式

```bash
rg -n '"""|# ' backend --glob '*.py' --glob '!**/.venv/**' --glob '!**/__pycache__/**'
./scripts/check_all.sh
```

## 风险与注意事项

- 本任务只修改注释和文档，避免误改可执行逻辑。
- Alembic 迁移文件中的 revision 标识、技术字段名和 API/ORM 等技术名词可以保留英文。
- 注释必须解释意图，不写无信息量注释。

## 完成记录

完成日期：2026-07-07

实际完成内容：

- 将后端 Python 源码中的英文模块 docstring、类 docstring、函数 docstring 和行内注释改为简体中文。
- 为当前函数补齐中文 docstring，覆盖功能、入参、返回值和异常场景。
- 更新 `docs/exec-plans/template.md`，要求每次执行前读取 `AGENTS.md`，并明确代码注释必须使用简体中文。
- 更新 `CHANGELOG.md`，记录本次注释语言和模板修正。
- 未修改业务逻辑、数据库结构、迁移结构或 API 行为。

验证结果：

```bash
rg -n '"""|# ' backend --glob '*.py' --glob '!**/.venv/**' --glob '!**/__pycache__/**'
# 结果显示业务注释和 docstring 已改为中文；Alembic 固定元数据字段如 Revision ID 保留英文。

./scripts/check_all.sh
# 4 passed, 1 warning
```

注意事项：

- 当前仍存在 FastAPI/Starlette TestClient 依赖弃用警告，不属于本任务范围。
- 后续执行计划必须显式继承 `AGENTS.md` 的中文注释强制规范。

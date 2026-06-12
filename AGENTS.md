# Repository Guidelines

## 项目结构与模块组织

本目录当前是一个基于 Flask 的后端工作区。`run.py` 是本地启动入口，`app/__init__.py` 负责应用初始化、扩展注册、蓝图挂载和数据库建表。
`app/controllers/` 按业务域拆分接口，目前包含 `auth.py`、`common.py`、`menu.py`、`system.py`、`timezone.py`、`user.py` 以及
`project/` 下的子模块。`app/models/` 存放 SQLAlchemy 模型，`app/utils/` 存放统一响应工具，配置位于 `config/config.py`，本地
SQLite 数据库位于 `instance/app.db`。

当前目录里未包含完整前端源码，`project/display` 路由会尝试渲染 `index.html`，但模板文件当前不在本目录。部分控制器依赖
`app/utils/mock_api.py`，该文件当前也不在本目录中；修改鉴权、菜单、系统管理相关接口前，先确认是准备补齐 mock 层，还是切换为真实实现。

## 代码风格与命名约定

1. Python 代码遵循 PEP 8，使用 4 空格缩进。模块、函数、变量使用 `snake_case`，类名使用 `CamelCase`。控制器中的蓝图对象统一命名为
   `bp`，保持与现有代码一致。接口响应优先复用 `app/utils/api.py` 中的 `success_api()`、`error_api()`、`table_api()`
   ，不要在不同控制器里随意发散返回结构。
2. 新增控制器时，优先按业务域落到 `app/controllers/` 或其子目录中，不要把无关接口堆进现有文件。涉及数据库模型时，修改
   `app/models/` 后同步检查 `app/__init__.py` 中的导入与建表副作用。
3. 发送后端请求时，使用layui的jquery模块

## 安全与配置注意事项

`config/config.py` 中的 `SECRET_KEY` 仍是示例值，部署前必须改为环境变量或部署配置注入。不要继续扩展明文密码方案；若接手认证逻辑，应改用哈希存储与校验。
`CORS(app)` 当前是开放配置，只适合开发阶段。`app/__init__.py` 里通过导入副作用执行 `db.create_all()`
，继续开发时应优先收敛为显式初始化流程，而不是扩大这个副作用。


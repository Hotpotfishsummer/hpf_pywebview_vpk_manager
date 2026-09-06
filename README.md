# L4D2 VPK Manager (PyWebView + Vue3 版本)

一个现代化的求生之路 2 (Left 4 Dead 2) VPK 文件管理工具，采用 **Vue3 + Python PyWebView** 架构，使用 Nuitka 打包为单一可执行文件。

## 功能特性

✨ **核心功能**
- 📁 浏览并选择 L4D2 游戏目录
- 📦 扫描并列出本地 VPK 文件和 Steam 创意工坊文件
- 💾 导出选定的 VPK 文件为 tar.zst 压缩包
- 📥 从 zip / 7z / tar.zst 压缩包导入 VPK 及其缩略图
- 🗑️ 删除或禁用 VPK 文件（自动同步处理关联图片/文本）
- 🌐 SFTP 远程文件同步：浏览、上传、下载、禁用/启用、重命名
- ⚙️ autoexec.cfg 自动应用模板并备份现有文件
- 🌍 完整的双语支持（英文和简体中文）
- ⚡ 快速的 VPK 元数据提取和缓存系统（自动失效重建）

🏗️ **技术特点**
- **前端：** Vue 3 + TypeScript + Pinia + Vite
- **后端：** Python 3.12 + PyWebView
- **国际化：** vue-i18n JSON 翻译文件
- **打包：** Nuitka 生成单一 .exe（Windows）
- **开发：** Hot reload + 并行前后端调试
- **测试：** 后端 pytest(240+ 用例,含覆盖率) + 前端 vitest 组件/单元测试 + GitHub Actions CI

## 快速开始

### 系统要求

- **操作系统：** Windows 10/11
- **Python：** 3.12
- **Node.js：** 20+（environment.yml 固定安装 Node 20；本机装有更高版本时前端工具链同样可用）
- **Conda：** Anaconda 或 Miniconda

### 1. 安装环境

```bash
# 从 environment.yml 创建 Conda 环境
conda env create -f environment.yml

# 激活环境
conda activate hpf-vpk-manager-pywebview

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 启动开发环境

```powershell
# 一键启动（前端 + 后端）
.\scripts\dev.ps1

# 或分别启动：
# 终端 1 - 启动 Vite dev server
cd frontend && npm run dev

# 终端 2 - 启动 Python 应用
python main.py
```

应用将在 PyWebView 窗口中打开。

### 3. 构建生产版本

```powershell
# 构建前端静态资源
.\scripts\build-frontend.ps1

# 打包为单一 .exe 文件
.\scripts\package-nuitka.ps1

# 输出文件：dist/main.exe
```

## 项目结构

```
├── main.py                        # PyWebView 应用入口
├── environment.yml                # Conda 环境配置
├── requirements.txt               # Python 依赖
├── pytest.ini                     # pytest 配置
│
├── tests/                         # 后端单元测试（pytest，240+ 用例）
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_naming.py
│   ├── test_dependency_consistency.py   # requirements.txt 与 environment.yml 一致性守卫
│   ├── test_metadata_service.py
│   ├── test_export_service.py
│   ├── test_import_service.py
│   ├── test_vpk_ops.py
│   └── ...（service 级与 i18n 键守卫等测试）
│
├── frontend/                      # Vue3 前端应用
│   ├── src/
│   │   ├── components/            # Vue 组件（AppHeader / StatusBanner / ActionBar / DirectorySelector /
│   │   │                          #   VpkFilesList / VpkFileItem / SftpBrowser / SettingsModal）
│   │   ├── stores/                # Pinia 状态管理（vpk-manager.ts）
│   │   ├── composables/           # useApi（PyWebView API 封装）/ useVpkSection
│   │   ├── types/                 # API 返回结果类型定义
│   │   ├── i18n/                  # 国际化配置和翻译文件
│   │   ├── App.vue                # 根组件
│   │   └── main.ts                # 前端入口
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── backend/                       # Python 后端
│   ├── api.py                     # PyWebView API 组装层（_PUBLIC_METHODS / 服务装配）
│   ├── api_sftp.py                # SFTP 相关 API 方法（SftpApiMixin）
│   ├── api_app.py                 # 目录/系统交互 API 方法（AppApiMixin）
│   ├── api_ops.py                 # VPK 核心操作 API 方法（VpkOpsApiMixin）
│   ├── models.py                  # 数据模型
│   ├── naming.py                  # 共享的 VPK 命名/清洗逻辑
│   └── services/
│       ├── vpk_metadata_service.py    # VPK 元数据提取（带 mtime/size 缓存失效校验）
│       ├── vpk_export_service.py      # VPK 导出和压缩
│       ├── vpk_import_service.py      # 压缩包（zip/7z/tar.zst）导入
│       ├── vpk_scan_service.py        # 本地/创意工坊 VPK 扫描
│       ├── vpk_localize_service.py    # 创意工坊文件本地化（复制+归档）
│       ├── vpk_upload_service.py      # VPK 及关联图片上传
│       ├── vpk_download_service.py    # VPK 及关联图片下载
│       ├── storage_service.py         # 用户偏好存储
│       ├── sftp_service.py            # SFTP 远程文件管理
│       └── config_service.py          # autoexec.cfg 配置管理
│
├── scripts/                       # 自动化脚本
│   ├── build-frontend.ps1         # 构建前端
│   ├── package-nuitka.ps1         # Nuitka 打包
│   └── dev.ps1                    # 启动开发环境
│
├── .vscode/
│   ├── launch.json                # VS Code 调试配置
│   └── tasks.json                 # VS Code 任务配置
│
└── .github/
    └── copilot-instructions.md    # GitHub Copilot 开发指南
```

## 前后端通信

应用采用 **PyWebView API 桥接** 模式进行前后端通信：

### 后端 API（Python）

`backend/api.py` 中的 `VpkManagerApi` 类（SFTP 方法在 `api_sftp.py` 的 `SftpApiMixin`）
向 pywebview 暴露同步方法，pywebview 在独立线程中调用并返回 Promise：

```python
class VpkManagerApi(SftpApiMixin):
    _PUBLIC_METHODS = {...}  # 前端可见方法白名单（有双向一致性守卫测试）
    def scan_vpk_files(self, directory: str) -> dict
    def export_vpks(self, file_paths: List[str], output_dir: str, better_naming: bool = False) -> dict
    def delete_vpk_file(self, file_path: str, disable: bool = True) -> dict
    # ... 共 22 个公开方法
```

### 前端调用（TypeScript）

统一经 `composables/useApi.ts` 的 `getApi()`（带类型定义，见 `types/api.ts`）调用：

```typescript
import { getApi } from '@/composables/useApi'

// 扫描 VPK 文件
const result = await getApi().scan_vpk_files('/path/to/l4d2')

// 导出文件
const exportResult = await getApi().export_vpks(
    ['/path/to/vpk1.vpk', '/path/to/vpk2.vpk'],
    '/home/user/Downloads'
)

// 删除文件
const deleteResult = await getApi().delete_vpk_file(
    '/path/to/vpk.vpk',
    true  // 禁用而不是删除
)
```

## 国际化

应用支持英文和简体中文，翻译存储在 JSON 文件中：

- `frontend/src/i18n/locales/en.json` - 英文翻译
- `frontend/src/i18n/locales/zh.json` - 中文翻译

在 Vue 模板中使用：

```vue
<template>
  <h1>{{ $t('appTitle') }}</h1>
  <p>{{ $t('error', { error: 'File not found' }) }}</p>
</template>
```

## 测试

后端单元测试基于 pytest（依赖已在 requirements.txt / environment.yml 中，含 pytest-cov）：

```bash
conda activate hpf-vpk-manager-pywebview
python -m pytest -q                      # 全量运行（240+ 用例）
python -m pytest -q --cov=backend        # 带覆盖率
```

测试覆盖：VPK 命名清洗与边界（`backend/naming.py`）、元数据提取与缓存失效、导入/导出全链路（含 7z 路径穿越防护）、SFTP 服务（mock）、上传/下载/本地化/扫描服务、依赖清单一致性守卫、未使用 i18n 键守卫、en/zh 占位符一致性、真实 VPK 构造的标题编码链路。全部使用临时目录或 mock，不触碰真实用户数据。

前端类型检查与单元测试（vitest，`npm run test`）：

```bash
cd frontend && npm run typecheck
cd frontend && npm run test
```

## 持续集成

`.github/workflows/ci.yml` 在 push/PR 时自动运行：后端 pytest（Python 3.12）、前端 vue-tsc 类型检查、前端 vite 构建。

## VS Code 快捷键和任务

### 调试快捷键

- `F5` - 启动复合调试配置（前端 + 后端同时运行）
- `Ctrl+Shift+D` - 打开调试面板

### 任务快捷键

- `Ctrl+Shift+B` - 运行默认构建任务（通常是构建前端）

### 自定义任务

运行 `Ctrl+Shift+P` 然后选择 "Tasks: Run Task"：

- `Frontend: Start Dev Server` - 启动 Vite dev server
- `Build: Nuitka Compile (Single File)` - Nuitka 打包
- `Dev: Start Full Environment` - 完整开发环境

## 开发工作流

### 添加新的 API 方法

1. 在 `backend/api.py` 的 `VpkManagerApi` 类中添加方法
2. 方法会自动通过 `window.api` 暴露给前端

```python
class VpkManagerApi:
    def my_new_method(self, param: str) -> dict:
        return {
            "success": True,
            "data": result
        }
```

3. 在前端调用：

```typescript
const result = await window.api.my_new_method('value')
```

### 添加新的 Vue 组件

1. 创建 `frontend/src/components/MyComponent.vue`
2. 在父组件中导入：

```vue
<script setup>
import MyComponent from '@/components/MyComponent.vue'
</script>

<template>
  <MyComponent />
</template>
```

### 添加翻译

1. 在 `frontend/src/i18n/locales/en.json` 和 `zh.json` 中添加键值对
2. 在模板中使用 `{{ $t('keyName') }}`

## 常见问题

### Q: 如何修改应用窗口大小？

**A:** 编辑 `main.py` 中的 `webview.create_window()` 参数：

```python
window = webview.create_window(
    title='L4D2 VPK Manager',
    url='http://localhost:5173',
    width=1400,      # 修改宽度
    height=900,      # 修改高度
    resizable=True   # 允许用户调整大小
)
```

### Q: 如何在开发时修改 Python 代码而无需重启应用？

**A:** 使用 Python 的自动重新加载工具：

```bash
pip install watchdog
python -m watchdog.auto_reload main.py
```

### Q: 生成的 .exe 文件为什么这么大？

**A:** Nuitka 将整个 Python 运行时和所有依赖嵌入到单一文件中。这是独立可执行文件的权衡。可以通过以下方式优化：

- 移除不必要的依赖
- 使用 `--follow-imports` 仅包含使用的模块
- 启用数据压缩选项

## 故障排查

### 应用启动失败 / 白屏

**A:** 查看日志文件 `Documents/L4D2-VPK-Manager/vpk_manager.log`（启动参数、前端资源定位、WebView 创建过程均有记录）。打包后若日志出现"找不到前端资源"，说明 `frontend/dist` 未随包携带，重新执行打包脚本即可。

### 偏好设置丢失或怀疑损坏

**A:** 偏好保存在 `Documents/L4D2-VPK-Manager/preferences.json`。文件损坏时应用启动会自动将其重命名为 `preferences.json.corrupt` 并以默认设置继续，原文件内容可在该副本中找回。

### SFTP 连接失败

**A:** 检查地址格式为 `host:port`（省略端口时默认 22）。连接默认 10 秒超时；网络较慢时可在代码中通过 `SftpService(connect_timeout=...)` 调大。所有连接错误都会写入日志。

### 开发模式（前端热更新）

**A:** 设置环境变量 `PYWEBVIEW_DEV=true` 后启动 Python 应用，将加载 Vite 开发服务器 `http://localhost:5173`（需先 `npm run dev`）。

## 配置文件

### `environment.yml`

Conda 环境配置，包含 Python 3.12、Node.js 和所有依赖。

### `requirements.txt`

Python 包依赖列表，包括 PyWebView、Nuitka、VPK 库等。

### `frontend/vite.config.js`

Vite 构建工具配置，定义开发服务器端口、输出目录等。

### `.vscode/launch.json`

VS Code 调试配置，支持 Python 和 Node.js 调试。

### `.vscode/tasks.json`

VS Code 任务配置，自动化构建和启动脚本。

## 贡献指南

欢迎提交问题和拉取请求！

## 许可证

MIT License - 详见 LICENSE 文件

## 相关项目

- [原始 Flet 版本](../hotpotfish_l4d2_vpk_manager/) - 基于 Flet GUI 框架的版本

---

**最后更新：** 2026年9月6日

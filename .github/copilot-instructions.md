# GitHub Copilot 指南 - L4D2 VPK 管理器 (PyWebView + Vue3)

## 项目概述

L4D2 VPK 管理器是一个从 Flet 框架迁移到 **Vue3 + PyWebView + Nuitka** 的现代应用程序。应用采用**前后端分离架构**，通过 PyWebView 的 JavaScript-Python 桥接实现通信。

## 架构规则

### 项目结构

```
hpf_pywebview_vpk_manager/
├── main.py                    # PyWebView 应用入口点
├── environment.yml            # Conda 环境配置
├── requirements.txt           # Python 依赖
├── frontend/                  # Vue3 前端应用
│   ├── src/
│   │   ├── components/        # Vue 组件（DirectorySelector, VpkFilesList 等）
│   │   ├── stores/            # Pinia 状态管理（vpk-manager.ts）
│   │   ├── composables/       # Vue Composition API 钩子
│   │   ├── i18n/              # 国际化系统（vue-i18n）
│   │   │   ├── index.ts       # i18n 初始化
│   │   │   └── locales/       # JSON 翻译文件（en.json, zh.json）
│   │   ├── App.vue            # 根组件
│   │   ├── main.ts            # 前端入口
│   │   └── style.css          # 全局样式
│   ├── index.html
│   ├── package.json
│   └── vite.config.js         # Vite 配置
├── backend/                   # Python 后端
│   ├── api.py                 # PyWebView API（暴露给前端的方法）
│   ├── models.py              # 数据模型（VpkFile, ApiResponse）
│   └── services/
│       ├── vpk_metadata_service.py    # VPK 元数据提取和缓存
│       ├── vpk_export_service.py      # VPK 导出和压缩
│       └── storage_service.py         # 用户偏好持久化（单例）
├── scripts/                   # 构建脚本
│   ├── build-frontend.ps1     # 构建前端
│   ├── package-nuitka.ps1     # 打包 Nuitka 单一可执行文件
│   └── dev.ps1                # 启动开发环境
└── .vscode/
    ├── launch.json            # 调试配置
    └── tasks.json             # 构建任务
```

### 前后端通信 (PyWebView API)

**通信方式：** JavaScript 通过 `window.api` 对象调用 Python 方法

**后端 API 定义** (`backend/api.py`):
- Python 类 `VpkManagerApi` 的所有公共方法自动暴露为 JavaScript 可调用的接口
- 方法调用以 snake_case 命名（例如 `scan_vpk_files`）
- 返回值自动 JSON 序列化

**前端调用示例：**
```javascript
const result = await window.api.scan_vpk_files('/path/to/l4d2')
```

**API 约定：**
- 同步方法返回值直接返回
- 异步方法返回 Promise（在 Vue 中使用 `await`）
- 错误返回格式：`{ success: false, error: "error message" }`
- 成功返回格式：`{ success: true, data: {...} }`

### 后端服务架构

**VpkManagerApi** (backend/api.py)
- 主 API 类，暴露给前端的接口
- 依赖注入三个服务实例
- 方法：
  - `get_last_directory()` - 获取上次选择的目录
  - `scan_vpk_files(directory)` - 扫描 VPK 文件
  - `export_vpks(file_paths, output_dir)` - 异步导出文件
  - `delete_vpk_file(file_path, disable)` - 删除或禁用文件

**服务层分离：**
- `VpkMetadataService` - VPK 文件元数据提取、缓存（使用 JSON）
- `VpkExportService` - VPK 文件导出、压缩（tar.zst 格式）
- `StorageService` - 用户偏好保存（单例模式，JSON 存储）

### 前端 Vue3 架构

**组件结构：**

```
App.vue (根组件)
├── DirectorySelector.vue      # 目录选择器
├── VpkFilesList.vue           # VPK 文件列表容器
│   └── VpkFileItem.vue        # 单个 VPK 文件项
└── 状态和动作面板
```

**状态管理 (Pinia Store)：**

文件：`frontend/src/stores/vpk-manager.ts`

```typescript
export const useVpkManagerStore = defineStore('vpkManager', () => {
  // 状态
  const currentDirectory = ref<string>('')
  const localVpkFiles = ref<VpkFile[]>([])
  const workshopVpkFiles = ref<VpkFile[]>([])
  const selectedLocalVpks = reactive(new Set<string>())  // 选中文件集合
  const selectedWorkshopVpks = reactive(new Set<string>())
  const isScanning = ref(false)
  const isExporting = ref(false)
  const isDeleting = ref(false)
  const errorMessage = ref<string>('')

  // 方法
  async function scanVpks(directory: string)
  async function exportVpks(outputDir: string)
  async function deleteVpks(disable: boolean = true)
  function toggleLocalVpkSelection(path: string)
  function getSelectedVpkPaths(): string[]
  // ...
})
```

**关键点：**
- 使用 `Composition API` 风格（不是 Options API）
- `Set` 用于快速查找选中的文件
- 异步操作（`scanVpks`, `exportVpks`）通过 `await window.api.*` 调用后端

**Composables 钩子：**

`frontend/src/composables/useApi.ts`
- `usePyWebViewApi()` - 检查 PyWebView API 可用性
- `useDownloadDirectory()` - 获取下载文件夹路径

### 国际化系统 (vue-i18n)

**迁移规则：**
- ARB 格式（`.arb` JSON）已转换为 `i18n/locales/` 下的 JSON 文件
- 键名规范：camelCase（例如 `directoryPathLabel`）
- 参数插值：`{placeholder}` 格式（例如 `"error": "错误: {error}"`）

**前端使用：**
```vue
<template>
  <p>{{ $t('appTitle') }}</p>
  <p>{{ $t('error', { error: 'File not found' }) }}</p>
</template>
```

**后端不处理翻译** - 所有用户面向的文本完全由前端负责，后端 API 仅返回数据。

**支持的语言：**
- `en` - 英文
- `zh` - 简体中文

**初始化：** 在 `frontend/src/i18n/index.ts` 配置，默认语言为 `zh`。

## 代码风格规则

### 前端 (Vue3 + TypeScript)

**导入语句**
```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { VpkFile } from '@/stores/vpk-manager'
// 路径别名 @ = src/
```

**组件命名**
- 文件：PascalCase（例如 `DirectorySelector.vue`）
- 组件标签：PascalCase（例如 `<DirectorySelector />` 或 `<vpk-file-item />`）

**函数和变量**
- 函数/方法：camelCase（例如 `scanVpks`, `toggleLocalVpkSelection`）
- 常量：UPPER_SNAKE_CASE
- 类型/接口：PascalCase（例如 `interface VpkFile`）

**样式**
- 使用 `<style scoped>` 限定作用域
- CSS 类名：kebab-case（例如 `.vpk-file-item`）
- 变量：CSS 变量用于主题色（可选）

**Composition API 规范**
```typescript
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useVpkManagerStore } from '@/stores/vpk-manager'

const store = useVpkManagerStore()
const localVariable = ref<string>('')

const computedValue = computed(() => {
  return localVariable.value.toUpperCase()
})

async function handleClick() {
  // ...
}
</script>
```

### 后端 (Python 3.12)

**导入语句**
- 标准库 → 第三方库 → 本地模块
- 使用绝对导入：`from backend.services.vpk_metadata_service import VpkMetadataService`
- 不要使用相对导入

**类和函数**
- 类：PascalCase（例如 `VpkManagerApi`）
- 方法/函数：snake_case（例如 `scan_vpk_files`）
- 私有方法：前缀 `_`（例如 `_generate_archive_name`）
- 常量：UPPER_SNAKE_CASE

**类型注解**
```python
from typing import List, Optional, Dict, Any

class VpkManagerApi:
    def scan_vpk_files(self, directory: str) -> dict:
        """扫描 VPK 文件"""
        pass

    async def export_vpks(self, file_paths: List[str], output_dir: str) -> dict:
        pass
```

**日志记录**
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"method_name: action - {result}")
logger.error(f"Error: {e}")
```

**异常处理**
```python
try:
    # 业务逻辑
    pass
except Exception as e:
    logger.error(f"Error: {e}")
    return {"success": False, "error": str(e)}
```

## PyWebView 集成规则

### 主入口 (main.py)

```python
import webview
from backend.api import VpkManagerApi

def main():
    api = VpkManagerApi()
    window = webview.create_window(
        title='L4D2 VPK Manager',
        url='frontend/dist/index.html',  # 生产环境使用构建的前端资源
        width=1200,
        height=800,
        resizable=True,
        js_api=api,  # 暴露 API 到 JavaScript
    )
    webview.start(debug=False)

if __name__ == '__main__':
    main()
```

**关键点：**
- `js_api=api` 将 Python 对象的公共方法暴露为 `window.api` 对象
- 开发时使用 `url='http://localhost:5173'` 连接 Vite dev server
- 生产时使用 `url='frontend/dist/index.html'` 使用静态资源

### 开发 vs 生产模式

**开发模式：**
1. 启动 Vite dev server（http://localhost:5173）
2. Python 应用启动，指向 dev server URL
3. 支持热更新（保存文件自动刷新）

**生产模式（Nuitka 打包）：**
1. 构建前端：`npm run build` → `frontend/dist/`
2. Nuitka 编译：`python -m nuitka --onefile ... main.py`
3. 生成单一 `.exe` 文件，资源嵌入其中

## 调试和日志

### 控制台输出
- **前端：** Vue DevTools（F12 浏览器开发工具）
- **后端：** PyWebView 启动的命令行窗口
- 日志文件：`vpk_manager.log`（后端日志）

### 启动配置
- VS Code：按 `F5` 启动复合调试配置（前端 + 后端同时运行）
- 或使用任务：`Dev: Start Full Environment`

### 常见调试技巧

**前端调试：**
```vue
<script setup>
console.log('Component mounted', store.localVpkFiles)
</script>
```

**后端调试：**
```python
print(f"DEBUG: vpk_files={vpk_files}")
import pdb; pdb.set_trace()  # 交互式调试
```

## 打包和部署 (Nuitka)

### 打包流程

```powershell
# 1. 构建前端
.\scripts\build-frontend.ps1

# 2. 打包 Nuitka（生成单一 .exe）
.\scripts\package-nuitka.ps1

# 输出：dist/main.exe
```

### Nuitka 配置

`scripts/package-nuitka.ps1` 使用的参数：

```powershell
python -m nuitka `
    --onefile                              # 单一可执行文件
    --windows-console-mode=gui             # 隐藏控制台窗口
    --include-data-dir=frontend/dist=...   # 嵌入前端资源
    --output-dir=dist                      # 输出目录
    main.py
```

**特点：**
- 单一 `.exe` 文件（不需要额外文件）
- 包含所有 Python 依赖和前端资源
- Windows 平台专用

### 分发

发布 `dist/main.exe` 给用户即可，无需 Python 环境。

## 开发工作流

### 本地开发

```bash
# 1. 创建 Conda 环境
conda env create -f environment.yml
conda activate hpf-vpk-manager-pywebview

# 2. 启动开发环境
.\scripts\dev.ps1

# 这将同时启动：
# - Vite dev server (http://localhost:5173)
# - Python PyWebView 应用
# 按 Ctrl+C 停止所有服务
```

### 编辑工作流

**添加新的 API 方法（后端）：**

1. 在 `backend/api.py` 的 `VpkManagerApi` 类中添加方法
2. 方法会自动暴露为 `window.api.method_name()`
3. 前端使用 `await window.api.method_name(args)` 调用

**添加新的 Vue 组件：**

1. 创建 `.vue` 文件在 `frontend/src/components/`
2. 在父组件中导入和使用（PascalCase）
3. 使用 `useVpkManagerStore()` 访问共享状态

**添加新的翻译键：**

1. 在 `frontend/src/i18n/locales/en.json` 和 `zh.json` 中添加键值对
2. 在模板中使用 `{{ $t('keyName') }}`
3. 如有参数：`{{ $t('keyName', { param: value }) }}`

## 常见问题和解决方案

### PyWebView API 不可用
**问题：** `window.api is undefined`
**原因：** PyWebView 尚未初始化完毕
**解决：** 在组件中使用 `usePyWebViewApi()` 钩子检查可用性

### 前端资源加载失败（生产环境）
**问题：** `frontend/dist/index.html not found`
**原因：** 未执行前端构建
**解决：** 运行 `scripts/build-frontend.ps1`

### Nuitka 编译失败
**问题：** 编译过程报错
**原因：** Python 版本不匹配或依赖缺失
**解决：** 确保在正确的 Conda 环境中，且所有依赖已安装

### 国际化文本显示不对
**问题：** 中文显示为乱码或英文
**原因：** i18n 未初始化或 JSON 文件编码错误
**解决：** 确保 JSON 文件采用 UTF-8 编码，i18n 在应用启动时初始化

### 后端文件操作权限错误
**问题：** `Permission denied` 错误
**原因：** VPK 文件被游戏或其他程序占用
**解决：** 确保 L4D2 未运行，检查文件权限

## 快速参考命令

```bash
# 环境管理
conda env create -f environment.yml
conda activate hpf-vpk-manager-pywebview
conda env remove -n hpf-vpk-manager-pywebview

# 前端开发
cd frontend
npm install                # 安装依赖
npm run dev                # 启动 Vite dev server
npm run build              # 生产构建

# 后端运行
python main.py             # 启动应用

# 打包和部署
.\scripts\build-frontend.ps1        # 构建前端
.\scripts\package-nuitka.ps1        # 打包 Nuitka

# 开发环境一键启动
.\scripts\dev.ps1

# 代码检查
pylint backend/            # Python 代码检查
npm run lint               # 前端 lint（如已配置）
```

## 版本控制

### Git 约定
- 分支：`feature/feature-name` 或 `fix/issue-name`
- 提交信息：现在时态，例如 "Add Vue3 migration" 或 "Fix API communication"
- `.gitignore` 已配置，避免提交临时文件、依赖、日志

## 文档生成规范

### ⛔ 禁止自动生成的文档

**除非用户明确要求，否则禁止自动生成以下类型的文件：**

**中文文档名：**
- 完成总结、总结文档、完成情况总结
- 检查清单、核查清单、任务清单
- 项目统计、数据统计
- 初始化报告、初始化总结
- 工作总结、工作报告
- 进度报告、进度总结
- 文件清单、文件列表
- 任务追踪、任务进度

**英文文档名（文件名）：**
- `COMPLETION_SUMMARY.md`、`COMPLETION_REPORT.md`
- `CHECKLIST.md`、`CHECKLIST.txt`
- `SUMMARY.md`、`SUMMARY.txt`
- `STATISTICS.md`、`STATS.md`
- `PROGRESS_REPORT.md`、`PROGRESS.md`
- `MANIFEST.md`、`MANIFEST.txt`
- `REPORT.md`、`OVERVIEW.md`
- `INVENTORY.md`、`TRACKING.md`
- 任何包含 `summary`、`checklist`、`report`、`manifest` 的文件名

### ✅ 允许生成的文档

仅在以下情况下生成文档：

1. **用户明确要求** - 例如"生成项目清单"、"写一份完成报告"
2. **核心项目文档** - 如 `README.md`、`QUICKSTART.md`、`ARCHITECTURE.md` 等
3. **开发指南** - 如 `copilot-instructions.md`（本文件）
4. **配置文件文档** - 如代码示例或 API 文档
5. **必要的项目文件** - 仅在用户要求或项目启动时创建

### 原因

- 过多的总结文档会造成项目混乱
- 检查清单和报告通常是临时的，不需要永久化
- 这些文档容易过时，维护成本高
- 用户可以随时要求生成特定文档

## 何时寻求人工帮助

- 重大架构变更
- 复杂的异步/并发问题
- 性能优化需求
- 添加新的系统集成（如数据库）
- 主要依赖更新

---

**最后更新：** 2026年1月21日  
**维护者：** GitHub Copilot

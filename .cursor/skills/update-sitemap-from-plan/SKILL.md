---
name: update-sitemap-from-plan
description: 在执行计划完成后，自动检测计划中新增的文件和目录，并将这些变化更新到 docs/sitemap.md。当用户确认执行计划完成或询问更新 sitemap 时使用此技能。
---

# 更新 Sitemap 从执行计划

在执行计划完成后，自动检测计划中新增的文件和目录结构，并将这些变化同步到 `docs/sitemap.md`。

## 使用场景

- 执行计划中的所有任务标记为 `completed`
- 用户确认执行计划已完成
- 用户明确要求更新 sitemap.md

## 工作流程

### 1. 识别执行计划文件

查找 `.cursor/plans/*.plan.md` 文件，识别最近完成或用户指定的执行计划。

### 2. 提取文件/目录信息

从执行计划中提取以下信息：

- **文件路径**：计划中提到的所有文件路径（如 `src/mcs_listener/clients/alimail_client.py`）
- **目录结构**：计划中描述的目录层级（如 `clients/`, `listeners/`）
- **文件说明**：文件的功能描述（从计划中的注释或说明提取）

**提取模式**：
- 查找形如 `**文件**：` 或 `文件：` 的行
- 查找代码块中的路径（如 `src/...`）
- 查找目录结构描述（如 `clients/` → `API 客户端层`）

### 3. 读取当前 sitemap.md

读取 `docs/sitemap.md`，理解其结构：
- 基于 `mcs-platform/` 目录的树形结构
- 使用缩进表示层级关系
- 包含文件说明注释

### 4. 合并新内容

将计划中的新文件/目录合并到 sitemap.md：

**合并规则**：
- 如果文件/目录已存在，检查是否需要更新说明
- 如果文件/目录不存在，按正确层级插入
- 保持 sitemap.md 的格式和缩进风格
- 保持目录结构的逻辑顺序

**插入位置**：
- 根据文件路径确定在 sitemap 中的位置
- 例如：`src/mcs_listener/clients/alimail_client.py` 应插入到 `services/mcs-listener/src/mcs_listener/` 下的 `clients/` 部分

### 5. 更新 sitemap.md

使用 `search_replace` 工具更新文件，确保：
- 保持原有的格式风格
- 正确的缩进（使用空格，与现有风格一致）
- 文件说明清晰简洁

## 实施步骤

### 步骤 1: 读取执行计划

```python
# 伪代码示例
plan_file = ".cursor/plans/{plan_name}.plan.md"
plan_content = read_file(plan_file)
```

### 步骤 2: 解析文件路径

从计划中提取所有文件路径：

```python
# 查找模式：
# - "**文件**：`path/to/file.py`"
# - "文件：`path/to/file.py`"
# - 代码块中的路径
# - 目录结构描述
```

### 步骤 3: 读取 sitemap.md

```python
sitemap_path = "docs/sitemap.md"
sitemap_content = read_file(sitemap_path)
```

### 步骤 4: 确定插入位置

根据文件路径在 sitemap 中找到对应的父目录位置：

```markdown
# 示例：插入 alimail_client.py
services/
├── mcs-listener/
│   └── src/
│       └── mcs_listener/
│           ├── clients/              # 找到这个位置
│           │   ├── __init__.py
│           │   └── alimail_client.py  # 插入这里
```

### 步骤 5: 执行更新

使用 `search_replace` 在正确位置插入新内容，保持格式一致。

## 注意事项

1. **路径映射**：
   - 计划中的路径可能是相对路径（如 `src/mcs_listener/...`）
   - sitemap 中使用完整路径（如 `services/mcs-listener/src/mcs_listener/...`）
   - 需要正确映射路径前缀

2. **格式一致性**：
   - 保持与现有 sitemap.md 相同的缩进风格
   - 文件说明使用简洁的中文描述
   - 目录结构使用树形符号（`├──`, `└──`）

3. **避免重复**：
   - 检查文件是否已存在于 sitemap 中
   - 如果存在，只更新说明（如果有变化）

4. **目录层级**：
   - 确保新目录在 sitemap 中有正确的层级关系
   - 如果父目录不存在，需要先创建父目录结构

## 示例

**执行计划片段**：
```markdown
#### 2. 实现 OAuth Token 管理器

**文件**：`src/mcs_listener/clients/alimail_client.py`

实现 `OAuthManager` 类...
```

**sitemap.md 更新**：
```markdown
│   │       └── mcs_listener/
│   │           ├── clients/
│   │           │   ├── __init__.py
│   │           │   └── alimail_client.py  # 阿里邮箱 API 客户端（OAuth + REST API）
```

## 验证

更新完成后，验证：
- [ ] 所有计划中提到的文件都已添加到 sitemap
- [ ] 文件位置正确（在正确的目录层级下）
- [ ] 格式与现有 sitemap 一致
- [ ] 没有重复条目
- [ ] 文件说明清晰准确

#!/usr/bin/env python3
"""
从执行计划文件中提取文件路径和目录结构。

用法:
    python scripts/extract_paths.py <plan_file>
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def extract_file_paths(content: str) -> List[Tuple[str, str]]:
    """
    从计划内容中提取文件路径和说明。
    
    返回: [(file_path, description), ...]
    """
    paths = []
    
    # 模式1: **文件**：`path/to/file.py`
    pattern1 = r'\*\*文件\*\*[：:]\s*`([^`]+)`'
    for match in re.finditer(pattern1, content):
        file_path = match.group(1)
        # 查找后续的描述（下一行或同一段）
        description = extract_description(content, match.end())
        paths.append((file_path, description))
    
    # 模式2: 文件：`path/to/file.py`
    pattern2 = r'文件[：:]\s*`([^`]+)`'
    for match in re.finditer(pattern2, content):
        file_path = match.group(1)
        if not any(p[0] == file_path for p in paths):  # 避免重复
            description = extract_description(content, match.end())
            paths.append((file_path, description))
    
    # 模式3: 代码块中的路径（如 "创建 `src/mcs_listener/clients/` 目录"）
    pattern3 = r'`([^`]+/.*?\.py)`|`([^`]+/.*?/)`'
    for match in re.finditer(pattern3, content):
        file_path = match.group(1) or match.group(2)
        if file_path and not any(p[0] == file_path for p in paths):
            description = extract_description(content, match.start())
            paths.append((file_path, description))
    
    return paths


def extract_description(content: str, start_pos: int) -> str:
    """从内容中提取文件描述（查找后续的说明文本）。"""
    # 查找后续的说明（通常在下一行或同一段落）
    lines = content[start_pos:start_pos + 500].split('\n')
    for line in lines[:3]:  # 只看后续3行
        line = line.strip()
        if line and not line.startswith('`') and not line.startswith('**'):
            # 移除常见的标记
            line = re.sub(r'^[-*]\s*', '', line)
            if len(line) > 5:  # 至少5个字符才认为是描述
                return line[:100]  # 限制长度
    return ""


def extract_directories(content: str) -> List[Tuple[str, str]]:
    """
    从计划内容中提取目录结构。
    
    返回: [(dir_path, description), ...]
    """
    dirs = []
    
    # 查找目录结构描述（如 "创建 `src/mcs_listener/clients/` 目录"）
    pattern = r'`([^`]+/)`'
    for match in re.finditer(pattern, content):
        dir_path = match.group(1)
        if dir_path and not any(d[0] == dir_path for d in dirs):
            description = extract_description(content, match.start())
            dirs.append((dir_path, description))
    
    return dirs


def main():
    if len(sys.argv) < 2:
        print("用法: python extract_paths.py <plan_file>", file=sys.stderr)
        sys.exit(1)
    
    plan_file = Path(sys.argv[1])
    if not plan_file.exists():
        print(f"错误: 文件不存在: {plan_file}", file=sys.stderr)
        sys.exit(1)
    
    content = plan_file.read_text(encoding='utf-8')
    
    files = extract_file_paths(content)
    dirs = extract_directories(content)
    
    print("# 提取的文件路径:")
    for file_path, desc in files:
        print(f"{file_path}\t{desc}")
    
    print("\n# 提取的目录路径:")
    for dir_path, desc in dirs:
        print(f"{dir_path}\t{desc}")


if __name__ == '__main__':
    main()

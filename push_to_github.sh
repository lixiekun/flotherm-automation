#!/bin/bash
# 一键推送 FloTHERM 自动化工具到 GitHub

set -e

REPO_NAME="flotherm-automation"
REPO_DESC="FloTHERM 自动化工具 - ECXML 参数修改、批量求解、参数化仿真"

echo "=========================================="
echo "  FloTHERM Automation - GitHub Push"
echo "=========================================="

# 检查 gh 是否已登录
if ! gh auth status &>/dev/null; then
    echo "请先登录 GitHub:"
    echo "  gh auth login"
    exit 1
fi

# 获取 GitHub 用户名
GH_USER=$(gh api user --jq '.login')
echo "GitHub 用户: $GH_USER"

# 创建远程仓库（如果不存在）
if ! gh repo view "$GH_USER/$REPO_NAME" &>/dev/null; then
    echo "创建仓库: $REPO_NAME"
    gh repo create "$REPO_NAME" \
        --public \
        --description "$REPO_DESC" \
        --confirm
    echo "仓库已创建: https://github.com/$GH_USER/$REPO_NAME"
else
    echo "仓库已存在: https://github.com/$GH_USER/$REPO_NAME"
fi

# 初始化 git（如果需要）
if [ ! -d ".git" ]; then
    echo "初始化 Git 仓库..."
    git init
    git branch -M main
fi

# 添加所有文件
echo "添加文件..."
git add -A

# 提交
if git diff --staged --quiet; then
    echo "没有新的更改"
else
    echo "提交更改..."
    git commit -m "feat: FloTHERM 自动化工具初始版本

- simple_solver.py: 简易求解脚本
- flotherm_solver.py: 完整求解脚本（生成 FloSCRIPT）
- ecxml_editor.py: ECXML 参数修改工具
- batch_simulation.py: 批量仿真案例生成器
- power_config.json: 功耗配置示例
- README.md: 使用说明

兼容 FloTHERM 2020.2 及其他版本"
fi

# 设置远程仓库并推送
echo "推送到 GitHub..."
git remote set-url origin "git@github.com:$GH_USER/$REPO_NAME.git" 2>/dev/null || \
    git remote add origin "git@github.com:$GH_USER/$REPO_NAME.git"

git push -u origin main

echo ""
echo "=========================================="
echo "  完成！"
echo "=========================================="
echo "仓库地址: https://github.com/$GH_USER/$REPO_NAME"
echo ""

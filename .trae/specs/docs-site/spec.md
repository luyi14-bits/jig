# Spec: MkDocs 文档站 (IDEA-042)

## Why
当前项目只有 README 和白皮书，没有可搜索的 API 参考文档站。对标 CrewAI（docs.crewai.com）/ PydanticAI（pydantic.ai）均标配文档站，缺少文档站影响开发者体验和外推效率。

## Meta
- **Priority**: P1
- **Est**: 2 days
- **Affected Specs**: IDEA-042

## What Changes
- ADDED: `mkdocs.yml` — MkDocs 配置文件（Material 主题）
- ADDED: `.github/workflows/mkdocs-deploy.yml` — GitHub Pages 自动部署
- ADDED: `docs/index.md` — 文档站首页
- ADDED: `docs/quickstart.md` — 快速开始文档
- ADDED: `docs/installation.md` — 安装指南

## Requirements

### R1: 文档站可本地构建
- **WHEN** 运行 `mkdocs build`
- **THEN** 生成 `site/` 目录，无错误

### R2: 文档站自动部署
- **WHEN** 推送 `main` 分支
- **THEN** GitHub Actions 触发部署到 GitHub Pages
- **AND** `https://luyi14-bits.github.io/jig` 可访问

### R3: API 参考页面
- **WHEN** 运行 `mkdocs build`
- **THEN** `site/api/index.html` 包含从 docstrings 提取的 API 参考

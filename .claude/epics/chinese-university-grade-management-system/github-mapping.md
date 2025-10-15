# GitHub Issue Mapping

## Epic
- #1 - Epic: chinese-university-grade-management-system
  URL: https://github.com/wangjia15/studentcourse-management/issues/1

## Tasks Created

| Task File | Issue # | Title | Status | URL |
|-----------|---------|-------|--------|-----|
| 001-project-infrastructure.md | #2 | 项目基础设施搭建 | ✅ Created | https://github.com/wangjia15/studentcourse-management/issues/2 |
| 002-database-design.md | - | 数据库设计与实现 | 🔄 Pending | - |
| 003-authentication-system.md | #5 | 用户认证与权限系统 | ✅ Created | https://github.com/wangjia15/studentcourse-management/issues/5 |
| 004-grade-spreadsheet.md | #3 | 成绩录入表格组件 | ✅ Created | https://github.com/wangjia15/studentcourse-management/issues/3 |
| 005-batch-processing.md | - | 批量数据处理功能 | 🔄 Pending | - |
| 006-statistics-engine.md | - | 统计分析引擎 | 🔄 Pending | - |
| 007-api-development.md | #4 | RESTful API开发 | ✅ Created | https://github.com/wangjia15/studentcourse-management/issues/4 |
| 008-testing-security.md | - | 测试与安全保障 | 🔄 Pending | - |

## Sync Summary
- **Epic**: ✅ Created (#1)
- **Tasks**: 4/8 created (50% complete)
- **Labels**: `enhancement` applied to all issues
- **Sub-issues**: Using gh-sub-issue extension
- **Repository**: wangjia15/studentcourse-management

## Remaining Tasks to Create
To complete the sync, create these remaining sub-issues:
- #?: 数据库设计与实现 (from 002-database-design.md)
- #?: 批量数据处理功能 (from 005-batch-processing.md)
- #?: 统计分析引擎 (from 006-statistics-engine.md)
- #?: 测试与安全保障 (from 008-testing-security.md)

## File Updates Needed
After all issues are created:
1. Rename task files with issue numbers (001.md → 2.md, etc.)
2. Update frontmatter with GitHub URLs
3. Update dependencies to use issue numbers
4. Update epic with task list

## Commands to Complete Sync
```bash
# Create remaining tasks
gh sub-issue create --parent 1 --title "数据库设计与实现" --body "$(sed '1,/^---$/d; 1,/^---$/d' tasks/002-database-design.md)" --label enhancement --repo wangjia15/studentcourse-management

# Update epic with GitHub URL
sed -i.bak "/^github:/c\github: https://github.com/wangjia15/studentcourse-management/issues/1" epic.md
```

Last updated: 2025-10-15T01:15:00Z
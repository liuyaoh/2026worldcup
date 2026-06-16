## 世界杯胜率预测系统

一个聚焦世界杯场景的胜率预测系统，支持三种工作模式：

- 赛前预测：根据球队资料、结构化数据与附加因素输出主胜/平局/客胜概率
- 比赛中动态预测：随着比分、红黄牌、xG、射正、危险进攻等变化实时重算胜率
- 历史回放模式：在没有真实直播时，按经典比赛事件时间线自动推进，验证胜率是否会随事件摆动

## 中文文档

中文文档已整理到 `docs/zh/` 目录，建议从这里开始阅读：

- [中文文档目录](file:///Users/lyhmacbook/Desktop/世界杯预测/world_cup/docs/zh/README.md)
- [01 快速开始](file:///Users/lyhmacbook/Desktop/世界杯预测/world_cup/docs/zh/01-快速开始.md)
- [04 历史回放模式（推荐先看）](file:///Users/lyhmacbook/Desktop/世界杯预测/world_cup/docs/zh/04-历史回放模式.md)

## 你现在能得到什么

- 世界杯 48 队结构化数据底座
- 球队图谱档案馆与中文摘要
- 赛前胜率预测结果
- 比赛中动态胜率与关键原因解释
- `football-data.org` 真实比赛数据接入
- 自动锁定当前直播比赛
- 历史回放模式自动推进事件

## 功能亮点

### 1. 世界杯 48 队数据底座

- 默认按世界杯 2026 的 48 支参赛队组织球队数据
- 数据文件：`backend/data/teams/fifa_teams.json`
- 支持分组、FIFA 基础数据、阵容摘要、关键球员与风格特点

### 2. 球队图谱档案馆

- 支持球队专属结构化档案展示
- 图谱内容按球队身份词过滤，避免串队
- 图谱英文摘要支持自动翻译成中文

### 3. 赛前预测

- 选择主队、客队与附加因素后输出：
  - 胜率结果
  - 战术分析
  - 关键胜负手
  - 终局判断

### 4. 比赛中动态预测

- 支持实时输入：
  - 当前分钟
  - 比分
  - 红黄牌
  - 控球率
  - 射正
  - xG
  - 危险进攻
  - 伤病/被动调整
- 系统会基于赛前基线实时更新胜率

### 5. 真实直播数据源

- 当前优先接入 `football-data.org`
- 支持：
  - 加载比赛列表
  - 自动锁定当前直播比赛
  - 自动轮询刷新
- 已按免费套餐限制做适配：
  - 默认轮询 30 秒
  - 可能存在比分延时
  - 可能缺少逐事件明细

### 6. 历史回放模式

- 适合在无直播比赛时演示“动态胜率”
- 目前内置经典比赛回放：
  - `2022 世界杯决赛：阿根廷 vs 法国`
- 特点：
  - 自动按事件推进
  - 不需要手动一条条改事件
  - 胜率会随回放过程自动变化

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.11

### 1. 配置环境变量

```bash
cp .env.example .env
```

建议至少配置以下内容：

```env
# LLM
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Zep 图谱
ZEP_API_KEY=your_zep_api_key

# 直播数据源
LIVE_DATA_PROVIDER=football-data
LIVE_DATA_POLL_INTERVAL_SECONDS=30
FOOTBALL_DATA_API_KEY=your_football_data_api_key_here
FOOTBALL_DATA_BASE_URL=https://api.football-data.org
FOOTBALL_DATA_WORLD_CUP_CODE=WC
```

### 2. 安装依赖

```bash
npm run setup:all
```

### 3. 启动项目

```bash
npm run dev
```

启动后访问：

- 前端：`http://localhost:3000`
- 后端：`http://localhost:5001`

## 使用方式

### 赛前预测

1. 选择主队与客队
2. 填写可选“特殊因素”
3. 点击“开始预测”

### 比赛中动态预测

1. 进入“比赛中动态预测”区域
2. 直接填写赛况数据
3. 或使用事件时间线控制台录入事件
4. 系统自动更新胜率与关键变化因素

### 真实直播模式

1. 在 `.env` 中配置 `FOOTBALL_DATA_API_KEY`
2. 在“真实直播数据源”区域加载比赛
3. 可开启自动直播同步

说明：

- 如果当前世界杯没有直播比赛，显示 0 场属于正常现象
- 这通常不是配置错误，而是当前没有可用直播场次

### 历史回放模式

1. 选择一场历史回放比赛
2. 点击“载入回放开场状态”
3. 点击“开始自动回放”
4. 系统会自动推进每个关键事件，并持续刷新胜率

## 项目结构

```text
world_cup/
├── frontend/                 # Vue 3 + Vite 前端
├── backend/                  # Flask 后端
│   ├── app/api/predict.py    # 主要预测与直播/回放接口
│   ├── app/services/         # 数据同步、图谱、直播、历史回放等服务
│   └── data/teams/           # 世界杯球队结构化数据
├── .env.example              # 环境变量示例
├── README.md
└── README-ZH.md
```

## 常见问题

### 1. 加载直播比赛列表时显示 0 场

可能原因：

- 世界杯尚未开赛
- 当前没有直播中的比赛
- `football-data` 免费版当前没有返回该赛事直播列表

建议：

- 先使用“历史回放模式”验证动态预测功能

### 2. 已结束比赛为什么不能直接自动回放真实事件

因为 `football-data` 免费版通常只返回基础比分与状态，不一定提供完整进球/换人/黄红牌事件流。

解决办法：

- 使用项目内置“历史回放模式”
- 或后续切换到支持逐事件明细的数据源

### 3. 为什么轮询默认是 30 秒

这是为了适配 `football-data` 免费套餐的频率限制，避免请求过快。

## 安全提示

- 不要把 `.env` 提交到仓库
- 不要公开泄露 `LLM_API_KEY`、`ZEP_API_KEY`、`FOOTBALL_DATA_API_KEY`

## 当前版本重点

当前版本已经围绕世界杯预测场景完成了以下升级：

- 世界杯 48 队数据收敛
- 球队图谱档案馆修复
- 图谱摘要中文化
- 动态胜率预测
- 真实直播数据源接入
- 自动锁定直播比赛
- 历史回放模式

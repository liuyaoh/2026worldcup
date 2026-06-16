## 05 API 文档

后端默认地址：`http://127.0.0.1:5001`

### 1）球队列表

- `GET /api/predict/teams?scope=world_cup_2026`
  - 返回世界杯 48 队（默认使用该范围）

### 2）球队详情（结构化档案 + 图谱）

- `GET /api/predict/team/<team_name>`
  - 返回结构化档案文本、图谱数据（可能异步入图谱）、中文化后的摘要等

### 3）赛前预测

- `POST /api/predict/analyze`
  - 输入：主队/客队、特殊因素等
  - 输出：胜率与解释

### 4）比赛中动态预测（手动状态）

- `POST /api/predict/live-analyze`
  - 输入：分钟、比分、红黄牌、xG、射正等结构化赛况
  - 输出：实时胜率、相对基线变化、关键因素、结论

### 5）真实直播数据源

- `GET /api/predict/live-source/providers`
  - 返回可用数据源、默认轮询等信息

- `GET /api/predict/live-source/matches?provider=football-data&live_only=true`
  - 返回可用比赛列表（可能为空，取决于赛事是否直播中）

- `POST /api/predict/live-source/analyze`
  - 输入：fixtureId（手动指定时）
  - 输出：拉取真实比赛状态并重算动态胜率

- `POST /api/predict/live-source/auto-analyze`
  - 输入：主队/客队（用于自动匹配），或为空时自动回退最优比赛
  - 输出：自动锁定比赛 + 拉取状态 + 动态胜率

### 6）历史回放

- `GET /api/predict/replays`
  - 返回内置历史回放列表

- `POST /api/predict/replay-analyze`
  - 输入：`replay_id` + `event_cursor`
  - 输出：按游标构建的比赛状态 + 动态胜率结果

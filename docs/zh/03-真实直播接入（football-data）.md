## 03 真实直播接入（football-data）

### 你能获得什么

当 `football-data` 有可用比赛数据时，本系统支持：

- 加载比赛列表
- 自动锁定当前直播比赛（不手动填 `fixtureId`）
- 按轮询间隔自动刷新比赛状态
- 将实时状态喂给动态预测引擎，自动更新胜率

### 免费套餐限制（重点）

`football-data` 免费版常见限制：

- 比分可能延时更新
- 每分钟请求次数有限（需要控制轮询频率）
- 逐事件明细（进球/换人/红黄牌等）可能缺失或不完整

因此项目默认：

- `LIVE_DATA_POLL_INTERVAL_SECONDS=30`（更稳，不容易触发频率问题）

### 配置方式

在 `world_cup/.env` 增加或确认以下变量：

```env
LIVE_DATA_PROVIDER=football-data
LIVE_DATA_POLL_INTERVAL_SECONDS=30

FOOTBALL_DATA_API_KEY=your_football_data_api_key_here
FOOTBALL_DATA_BASE_URL=https://api.football-data.org
FOOTBALL_DATA_WORLD_CUP_CODE=WC
```

修改 `.env` 后需要重启后端服务。

### 为什么“加载直播列表是 0 场”

这通常不是配置错误，而是：

- 世界杯未开赛
- 当前没有直播中的比赛
- 数据源暂时没返回对应赛事的直播列表

建议：

- 用“历史回放模式”验证动态预测链路（见 [04 历史回放模式](./04-历史回放模式.md)）
- 等赛事进入直播窗口后再测试自动同步

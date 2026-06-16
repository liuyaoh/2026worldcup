<template>
  <div class="predict-container">
    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <div class="nav-brand">🏆 世界杯胜率预测中心</div>
      <div class="nav-links">
        <button class="nav-btn" @click="$router.push('/team-detail')">
          <span class="icon">🔍</span> 查看图谱档案馆
        </button>
        <span class="version-text">v1.0 (AI Powered)</span>
      </div>
    </nav>

    <div class="main-content">
      <h1 class="page-title">世界杯球队胜率预测系统</h1>
      <p class="page-desc">
        上传球队资料库后，可进行赛前预测，也可在比赛进行中根据比分、红黄牌和场面数据实时重算动态胜率。
      </p>

      <div class="dashboard">
        <!-- 左侧：球队资料上传 -->
        <div class="panel left-panel">
          <h2 class="panel-title">📚 球队情报库</h2>
          
          <div class="upload-zone"
               :class="{ 'drag-over': isDragOver }"
               @dragover.prevent="isDragOver = true"
               @dragleave.prevent="isDragOver = false"
               @drop.prevent="handleDrop"
               @click="$refs.fileInput.click()">
            <input type="file" ref="fileInput" multiple accept=".txt,.md" style="display:none" @change="handleFileSelect">
            <div class="upload-icon">📁</div>
            <p>点击或拖拽文件上传</p>
            <span class="upload-hint">支持 .txt, .md，文件名将作为球队名（如: 阿根廷.txt）</span>
          </div>

          <button class="sync-btn" @click="syncFifaTeams" :disabled="isSyncingFifa">
            {{ isSyncingFifa ? '正在导入世界杯48支参赛队...' : '导入世界杯48支参赛队' }}
          </button>
          <p class="sync-hint">会按世界杯 2026 的 48 支参赛队名单抓取 FIFA 官方球队页数据，并写入结构化球队数据库。</p>

          <div class="team-list">
            <h3>已入库球队 ({{ availableTeams.length }})</h3>
            <div class="teams-grid">
              <span v-for="team in availableTeams" :key="team" class="team-tag">{{ team }}</span>
            </div>
            <div v-if="availableTeams.length === 0" class="empty-hint">暂无球队数据，请先上传资料。</div>
          </div>
        </div>

        <!-- 右侧：预测控制台 -->
        <div class="panel right-panel">
          <h2 class="panel-title">⚽ 赛事预测台</h2>
          
          <div class="match-setup">
            <div class="team-select-group">
              <div class="select-box">
                <label>主队 (Team A)</label>
                <select v-model="matchConfig.teamA">
                  <option value="">-- 请选择主队 --</option>
                  <option v-for="team in availableTeams" :key="'A-'+team" :value="team">{{ team }}</option>
                </select>
              </div>
              <div class="vs-badge">VS</div>
              <div class="select-box">
                <label>客队 (Team B)</label>
                <select v-model="matchConfig.teamB">
                  <option value="">-- 请选择客队 --</option>
                  <option v-for="team in availableTeams" :key="'B-'+team" :value="team">{{ team }}</option>
                </select>
              </div>
            </div>

            <div class="factors-input">
              <label>特殊因素 / 附加说明 (可选)</label>
              <textarea v-model="matchConfig.factors" rows="3" placeholder="例如：阿根廷队梅西状态极佳；法国队核心中场因伤缺阵；比赛当天下大雨..."></textarea>
            </div>

            <button class="predict-btn" @click="startPrediction" :disabled="!canPredict || isPredicting">
              <span v-if="isPredicting" class="spinner"></span>
              {{ isPredicting ? 'AI 正在深度推演中...' : '🚀 开始预测' }}
            </button>

            <div class="live-mode-divider"></div>

            <div class="live-panel">
              <h3 class="sub-panel-title">比赛中动态预测</h3>
              <p class="live-hint">
                输入当前分钟、比分和场面数据后，系统会基于赛前基线实时重算主胜、平局、客胜概率。
              </p>

              <div class="source-panel">
                <h4 class="event-title">真实直播数据源</h4>
                <p class="event-hint">
                  接入外部比赛直播接口后，这里可以自动拉取真实比赛的分钟、比分和基础事件，并持续自动调整胜率。
                </p>
                <div class="source-notice">
                  当前默认按 `football-data.org` 免费套餐适配：世界杯可免费使用，但比分存在延时，且通常不提供首发、红牌等深度球员数据。建议轮询间隔保持 30 秒或更高。
                </div>

                <div class="source-grid">
                  <div class="live-field">
                    <label>数据源</label>
                    <select v-model="liveSourceConfig.provider">
                      <option v-for="provider in liveSourceProviders" :key="provider.id" :value="provider.id" :disabled="!provider.configured">
                        {{ provider.label }}{{ provider.configured ? '' : '（未配置）' }}
                      </option>
                    </select>
                  </div>
                  <div class="live-field">
                    <label>比赛日期</label>
                    <input v-model="liveSourceConfig.date" type="date">
                  </div>
                  <div class="live-field">
                    <label>比赛范围</label>
                    <select v-model="liveSourceConfig.liveOnly">
                      <option :value="true">仅直播中</option>
                      <option :value="false">按日期查全部</option>
                    </select>
                  </div>
                  <div class="live-field">
                    <label>轮询秒数</label>
                    <input v-model.number="liveSourceConfig.pollSeconds" type="number" min="15" max="120">
                  </div>
                  <div class="live-field">
                    <label>比赛锁定方式</label>
                    <select v-model="liveSourceConfig.autoSelectCurrent">
                      <option :value="true">自动锁定当前直播世界杯比赛</option>
                      <option :value="false">手动指定比赛</option>
                    </select>
                  </div>
                </div>

                <div class="source-actions">
                  <button class="ghost-btn source-btn" @click="fetchLiveSourceMatches" :disabled="isLoadingLiveMatches">
                    {{ isLoadingLiveMatches ? '正在加载比赛...' : '加载直播比赛列表' }}
                  </button>
                  <button class="ghost-btn source-btn" @click="syncLiveSourcePrediction" :disabled="(!liveSourceConfig.autoSelectCurrent && !liveSourceConfig.fixtureId) || isSyncingLiveSource">
                    {{ isSyncingLiveSource ? '同步中...' : (liveSourceConfig.autoSelectCurrent ? '自动锁定并同步直播比赛' : '同步真实直播数据') }}
                  </button>
                  <button class="ghost-btn source-btn" @click="toggleLiveSourceAutoSync" :disabled="!liveSourceConfig.autoSelectCurrent && !liveSourceConfig.fixtureId">
                    {{ liveSourceConfig.autoSync ? '停止自动直播同步' : '开启自动直播同步' }}
                  </button>
                </div>

                <div v-if="!liveSourceConfig.autoSelectCurrent" class="live-field fixture-select">
                  <label>直播比赛</label>
                  <select v-model="liveSourceConfig.fixtureId">
                    <option value="">-- 请选择直播比赛 --</option>
                    <option v-for="match in liveSourceMatches" :key="match.fixture_id" :value="match.fixture_id">
                      {{ formatLiveMatchOption(match) }}
                    </option>
                  </select>
                </div>

                <div v-if="liveSourceStatus" class="source-status">{{ liveSourceStatus }}</div>

                <div v-if="liveSourceMeta" class="live-meta source-meta">
                  <span class="meta-chip">{{ liveSourceMeta.competition_name || '直播比赛' }}</span>
                  <span class="meta-chip">{{ liveSourceMeta.status || '未知状态' }}</span>
                  <span class="meta-chip">比赛ID {{ liveSourceMeta.fixture_id }}</span>
                  <span class="meta-chip" v-if="liveSourceConfig.autoSelectCurrent">自动锁定中</span>
                  <span class="meta-chip" v-if="liveSourceMeta.venue">{{ liveSourceMeta.venue }}</span>
                </div>
              </div>

              <div class="source-panel replay-panel">
                <h4 class="event-title">历史回放模式</h4>
                <p class="event-hint">
                  选择一场经典比赛后，系统会按历史事件时间线自动推进，模拟直播过程中的胜率摆动，不需要你手动逐条修改事件。
                </p>
                <div class="source-grid replay-grid">
                  <div class="live-field replay-select">
                    <label>回放比赛</label>
                    <select v-model="historicalReplayConfig.replayId">
                      <option value="">-- 请选择历史回放比赛 --</option>
                      <option v-for="replay in historicalReplays" :key="replay.id" :value="replay.id">
                        {{ replay.title }} · {{ replay.subtitle }}
                      </option>
                    </select>
                  </div>
                  <div class="live-field">
                    <label>推进速度</label>
                    <select v-model.number="historicalReplayConfig.speedMs">
                      <option :value="1200">快速回放</option>
                      <option :value="2200">标准回放</option>
                      <option :value="3500">慢速讲解</option>
                    </select>
                  </div>
                </div>

                <div class="source-actions">
                  <button class="ghost-btn replay-btn" @click="loadHistoricalReplaySnapshot(0)" :disabled="!historicalReplayConfig.replayId || isLoadingHistoricalReplay">
                    {{ isLoadingHistoricalReplay ? '载入中...' : '载入回放开场状态' }}
                  </button>
                  <button class="ghost-btn replay-btn" @click="toggleHistoricalReplayPlayback" :disabled="!historicalReplayConfig.replayId || isLoadingHistoricalReplay">
                    {{ isHistoricalReplayPlaying ? '暂停自动回放' : '开始自动回放' }}
                  </button>
                  <button class="ghost-btn replay-btn" @click="advanceHistoricalReplayStep" :disabled="!historicalReplayConfig.replayId || isLoadingHistoricalReplay">
                    下一事件
                  </button>
                  <button class="ghost-btn replay-btn" @click="resetHistoricalReplay" :disabled="!historicalReplayMeta">
                    重置回放
                  </button>
                </div>

                <div v-if="historicalReplayMeta" class="live-meta source-meta">
                  <span class="meta-chip">{{ historicalReplayMeta.title }}</span>
                  <span class="meta-chip">{{ historicalReplayMeta.subtitle }}</span>
                  <span class="meta-chip">已推进 {{ historicalReplayCursor }} / {{ historicalReplayMeta.event_count }}</span>
                  <span class="meta-chip">{{ historicalReplayMeta.final_score }}</span>
                </div>

                <div v-if="historicalReplayCurrentEvent" class="replay-current-event">
                  当前推进事件：第 {{ historicalReplayCurrentEvent.minute }} 分钟，{{ formatEventLabel(historicalReplayCurrentEvent) }}
                </div>
                <div v-if="historicalReplayStatus" class="source-status">{{ historicalReplayStatus }}</div>
              </div>

              <div class="live-grid">
                <div class="live-field">
                  <label>当前分钟</label>
                  <input v-model.number="liveMatchState.minute" type="number" min="0" max="130" placeholder="例如 67">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamA || '主队' }} 比分</label>
                  <input v-model.number="liveMatchState.scoreA" type="number" min="0" placeholder="0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamB || '客队' }} 比分</label>
                  <input v-model.number="liveMatchState.scoreB" type="number" min="0" placeholder="0">
                </div>
                <div class="live-field">
                  <label>场上势头</label>
                  <select v-model="liveMatchState.momentum">
                    <option value="balanced">均势</option>
                    <option value="team_a">{{ matchConfig.teamA || '主队' }}</option>
                    <option value="team_b">{{ matchConfig.teamB || '客队' }}</option>
                  </select>
                </div>

                <div class="live-field">
                  <label>{{ matchConfig.teamA || '主队' }} 红牌</label>
                  <input v-model.number="liveMatchState.redCardsA" type="number" min="0" placeholder="0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamB || '客队' }} 红牌</label>
                  <input v-model.number="liveMatchState.redCardsB" type="number" min="0" placeholder="0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamA || '主队' }} 黄牌</label>
                  <input v-model.number="liveMatchState.yellowCardsA" type="number" min="0" placeholder="0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamB || '客队' }} 黄牌</label>
                  <input v-model.number="liveMatchState.yellowCardsB" type="number" min="0" placeholder="0">
                </div>

                <div class="live-field">
                  <label>{{ matchConfig.teamA || '主队' }} 控球率 (%)</label>
                  <input v-model.number="liveMatchState.possessionA" type="number" min="0" max="100" placeholder="50">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamB || '客队' }} 控球率 (%)</label>
                  <input v-model.number="liveMatchState.possessionB" type="number" min="0" max="100" placeholder="50">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamA || '主队' }} 射正</label>
                  <input v-model.number="liveMatchState.shotsOnTargetA" type="number" min="0" placeholder="0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamB || '客队' }} 射正</label>
                  <input v-model.number="liveMatchState.shotsOnTargetB" type="number" min="0" placeholder="0">
                </div>

                <div class="live-field">
                  <label>{{ matchConfig.teamA || '主队' }} xG</label>
                  <input v-model.number="liveMatchState.xgA" type="number" min="0" step="0.1" placeholder="0.0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamB || '客队' }} xG</label>
                  <input v-model.number="liveMatchState.xgB" type="number" min="0" step="0.1" placeholder="0.0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamA || '主队' }} 危险进攻</label>
                  <input v-model.number="liveMatchState.dangerousAttacksA" type="number" min="0" placeholder="0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamB || '客队' }} 危险进攻</label>
                  <input v-model.number="liveMatchState.dangerousAttacksB" type="number" min="0" placeholder="0">
                </div>

                <div class="live-field">
                  <label>{{ matchConfig.teamA || '主队' }} 伤病/被动调整</label>
                  <input v-model.number="liveMatchState.injuriesA" type="number" min="0" placeholder="0">
                </div>
                <div class="live-field">
                  <label>{{ matchConfig.teamB || '客队' }} 伤病/被动调整</label>
                  <input v-model.number="liveMatchState.injuriesB" type="number" min="0" placeholder="0">
                </div>
              </div>

              <div class="factors-input">
                <label>实时事件备注 (可选)</label>
                <textarea
                  v-model="liveMatchState.notes"
                  rows="3"
                  placeholder="例如：第63分钟主队中锋伤退；第70分钟客队连续形成高压；VAR取消进球..."
                ></textarea>
              </div>

              <div class="event-composer">
                <h4 class="event-title">事件时间线控制台</h4>
                <p class="event-hint">
                  你可以直接录入比分数据，也可以通过下面的事件按钮模拟直播过程。每次添加事件后，系统会自动更新赛况并重算胜率。
                </p>

                <div class="event-toolbar">
                  <div class="live-field">
                    <label>事件分钟</label>
                    <input v-model.number="eventDraft.minute" type="number" min="0" max="130" placeholder="如 68">
                  </div>
                  <div class="live-field">
                    <label>事件归属</label>
                    <select v-model="eventDraft.team">
                      <option value="team_a">{{ matchConfig.teamA || '主队' }}</option>
                      <option value="team_b">{{ matchConfig.teamB || '客队' }}</option>
                    </select>
                  </div>
                  <div class="live-field">
                    <label>事件说明</label>
                    <input v-model="eventDraft.description" type="text" placeholder="如：定位球制造混乱">
                  </div>
                </div>

                <div class="event-actions">
                  <button class="event-btn goal" @click="applyLiveEvent('goal')" :disabled="!canPredict">主/客队进球</button>
                  <button class="event-btn red" @click="applyLiveEvent('red_card')" :disabled="!canPredict">红牌</button>
                  <button class="event-btn yellow" @click="applyLiveEvent('yellow_card')" :disabled="!canPredict">黄牌</button>
                  <button class="event-btn injury" @click="applyLiveEvent('injury')" :disabled="!canPredict">伤病</button>
                  <button class="event-btn shot" @click="applyLiveEvent('shot_on_target')" :disabled="!canPredict">射正</button>
                  <button class="event-btn chance" @click="applyLiveEvent('xg_chance')" :disabled="!canPredict">高质量机会</button>
                  <button class="event-btn danger" @click="applyLiveEvent('dangerous_attack')" :disabled="!canPredict">危险进攻</button>
                  <button class="event-btn momentum" @click="applyLiveEvent('momentum')" :disabled="!canPredict">场上势头</button>
                </div>

                <div class="timeline-card">
                  <div class="timeline-head">
                    <h4 class="event-title">已记录事件 ({{ liveEvents.length }})</h4>
                    <button class="ghost-btn" @click="clearLiveEvents" :disabled="liveEvents.length === 0">清空时间线</button>
                  </div>
                  <div v-if="liveEvents.length === 0" class="timeline-empty">还没有事件。你可以先录入一个进球、红牌或伤病事件试试。</div>
                  <div v-else class="timeline-list">
                    <div v-for="event in liveEvents" :key="event.id" class="timeline-item">
                      <div>
                        <div class="timeline-minute">第 {{ event.minute }} 分钟</div>
                        <div class="timeline-text">{{ formatEventLabel(event) }}</div>
                      </div>
                      <button class="ghost-btn" @click="removeLiveEvent(event.id)">删除</button>
                    </div>
                  </div>
                </div>
              </div>

              <button class="predict-btn live-btn" @click="startLivePrediction" :disabled="!canPredict || isLivePredicting">
                <span v-if="isLivePredicting" class="spinner"></span>
                {{ isLivePredicting ? '实时模型计算中...' : '📡 开始动态预测' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 预测结果展示区 -->
      <div v-if="predictionResult" class="result-section">
        <h2 class="result-title">📊 AI 预测战报</h2>
        
        <div class="win-rate-bars">
          <div class="rate-bar team-a" :style="{ width: predictionResult.win_rate_a }">
            <span class="rate-label">{{ matchConfig.teamA }} 胜: {{ predictionResult.win_rate_a }}</span>
          </div>
          <div class="rate-bar draw" :style="{ width: predictionResult.draw_rate }">
            <span class="rate-label">平局: {{ predictionResult.draw_rate }}</span>
          </div>
          <div class="rate-bar team-b" :style="{ width: predictionResult.win_rate_b }">
            <span class="rate-label">{{ matchConfig.teamB }} 胜: {{ predictionResult.win_rate_b }}</span>
          </div>
        </div>

        <div class="analysis-grid">
          <div class="analysis-card">
            <h3>战术分析</h3>
            <p>{{ predictionResult.tactical_analysis }}</p>
          </div>
          <div class="analysis-card">
            <h3>关键胜负手</h3>
            <ul>
              <li v-for="(factor, index) in predictionResult.key_factors" :key="index">{{ factor }}</li>
            </ul>
          </div>
        </div>

        <div class="final-verdict">
          <h3>终局断言</h3>
          <p class="verdict-text">{{ predictionResult.final_prediction }}</p>
        </div>
      </div>

      <div v-if="livePredictionResult" class="result-section live-result-section">
        <h2 class="result-title">📡 比赛中动态预测</h2>

        <div class="live-meta">
          <span class="meta-chip">{{ livePredictionResult.scoreline }}</span>
          <span class="meta-chip">第 {{ livePredictionResult.minute }} 分钟</span>
          <span class="meta-chip">{{ livePredictionResult.momentum_label }}</span>
        </div>

        <div class="win-rate-bars">
          <div class="rate-bar team-a" :style="{ width: livePredictionResult.win_rate_a }">
            <span class="rate-label">{{ matchConfig.teamA }} 胜: {{ livePredictionResult.win_rate_a }}</span>
          </div>
          <div class="rate-bar draw" :style="{ width: livePredictionResult.draw_rate }">
            <span class="rate-label">平局: {{ livePredictionResult.draw_rate }}</span>
          </div>
          <div class="rate-bar team-b" :style="{ width: livePredictionResult.win_rate_b }">
            <span class="rate-label">{{ matchConfig.teamB }} 胜: {{ livePredictionResult.win_rate_b }}</span>
          </div>
        </div>

        <div class="delta-grid">
          <div class="delta-card">
            <h3>{{ matchConfig.teamA }} 胜率变化</h3>
            <p>{{ livePredictionResult.delta_win_rate_a }}</p>
            <span>赛前基线 {{ livePredictionResult.baseline_win_rate_a }}</span>
          </div>
          <div class="delta-card">
            <h3>平局变化</h3>
            <p>{{ livePredictionResult.delta_draw_rate }}</p>
            <span>赛前基线 {{ livePredictionResult.baseline_draw_rate }}</span>
          </div>
          <div class="delta-card">
            <h3>{{ matchConfig.teamB }} 胜率变化</h3>
            <p>{{ livePredictionResult.delta_win_rate_b }}</p>
            <span>赛前基线 {{ livePredictionResult.baseline_win_rate_b }}</span>
          </div>
        </div>

        <div class="analysis-grid">
          <div class="analysis-card">
            <h3>实时走势解读</h3>
            <p>{{ livePredictionResult.live_summary }}</p>
          </div>
          <div class="analysis-card">
            <h3>关键变化因素</h3>
            <ul>
              <li v-for="(factor, index) in livePredictionResult.key_factors" :key="index">{{ factor }}</li>
            </ul>
          </div>
        </div>

        <div v-if="livePredictionResult.recent_events?.length" class="analysis-card recent-events-card">
          <h3>最近关键事件</h3>
          <ul>
            <li v-for="(event, index) in livePredictionResult.recent_events" :key="index">{{ event }}</li>
          </ul>
        </div>

        <div class="final-verdict">
          <h3>实时判断</h3>
          <p class="verdict-text">{{ livePredictionResult.final_prediction }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onBeforeUnmount } from 'vue'

const availableTeams = ref([])
const isDragOver = ref(false)
const isPredicting = ref(false)
const isLivePredicting = ref(false)
const isSyncingLiveSource = ref(false)
const isLoadingLiveMatches = ref(false)
const isLoadingHistoricalReplay = ref(false)
const isSyncingFifa = ref(false)
const predictionResult = ref(null)
const livePredictionResult = ref(null)
const liveEvents = ref([])
let liveAutoTimer = null
let liveSourcePollTimer = null
let historicalReplayTimer = null
let suppressLocalAutoPredictUntil = 0

const matchConfig = ref({
  teamA: '',
  teamB: '',
  factors: ''
})

const liveMatchState = ref({
  minute: 0,
  scoreA: 0,
  scoreB: 0,
  redCardsA: 0,
  redCardsB: 0,
  yellowCardsA: 0,
  yellowCardsB: 0,
  possessionA: 50,
  possessionB: 50,
  shotsOnTargetA: 0,
  shotsOnTargetB: 0,
  xgA: 0,
  xgB: 0,
  dangerousAttacksA: 0,
  dangerousAttacksB: 0,
  injuriesA: 0,
  injuriesB: 0,
  momentum: 'balanced',
  notes: ''
})

const eventDraft = ref({
  minute: 0,
  team: 'team_a',
  description: ''
})

const liveSourceProviders = ref([])
const liveSourceMatches = ref([])
const liveSourceMeta = ref(null)
const liveSourceStatus = ref('')
const liveSourceConfig = ref({
  provider: 'football-data',
  date: new Date().toISOString().slice(0, 10),
  liveOnly: true,
  fixtureId: '',
  autoSelectCurrent: true,
  autoSync: false,
  pollSeconds: 30
})

const historicalReplays = ref([])
const historicalReplayMeta = ref(null)
const historicalReplayStatus = ref('')
const historicalReplayCurrentEvent = ref(null)
const historicalReplayCursor = ref(0)
const isHistoricalReplayPlaying = ref(false)
const historicalReplayConfig = ref({
  replayId: '',
  speedMs: 2200
})

const canPredict = computed(() => {
  return matchConfig.value.teamA && matchConfig.value.teamB && matchConfig.value.teamA !== matchConfig.value.teamB
})

const eventTypeLabels = {
  goal: '进球',
  red_card: '红牌',
  yellow_card: '黄牌',
  injury: '伤病',
  shot_on_target: '射正',
  xg_chance: '高质量机会',
  dangerous_attack: '危险进攻',
  momentum: '场上势头'
}

const teamLabelBySide = (side) => {
  return side === 'team_b'
    ? (matchConfig.value.teamB || '客队')
    : (matchConfig.value.teamA || '主队')
}

const formatEventLabel = (event) => {
  const suffix = event.description ? `：${event.description}` : ''
  return `${teamLabelBySide(event.team)}${eventTypeLabels[event.type] || event.type}${suffix}`
}

const formatLiveMatchOption = (match) => {
  const status = match.status || '未知状态'
  const minute = match.minute ? `${match.minute}'` : ''
  const score = `${match.score_a ?? 0}:${match.score_b ?? 0}`
  return `${match.label}  ${score}  ${status}${minute ? ` ${minute}` : ''}`
}

const sortLiveEvents = () => {
  liveEvents.value.sort((a, b) => b.minute - a.minute || b.createdAt - a.createdAt)
}

const syncLiveStateFromEvents = () => {
  const baseState = {
    ...liveMatchState.value,
    scoreA: 0,
    scoreB: 0,
    redCardsA: 0,
    redCardsB: 0,
    yellowCardsA: 0,
    yellowCardsB: 0,
    shotsOnTargetA: 0,
    shotsOnTargetB: 0,
    xgA: 0,
    xgB: 0,
    dangerousAttacksA: 0,
    dangerousAttacksB: 0,
    injuriesA: 0,
    injuriesB: 0,
    momentum: 'balanced'
  }

  let latestMinute = 0
  let latestMomentum = 'balanced'
  const orderedEvents = [...liveEvents.value].sort((a, b) => a.minute - b.minute || a.createdAt - b.createdAt)

  for (const event of orderedEvents) {
    const isTeamA = event.team === 'team_a'
    latestMinute = Math.max(latestMinute, Number(event.minute) || 0)
    if (event.type === 'goal') {
      if (isTeamA) baseState.scoreA += 1
      else baseState.scoreB += 1
    } else if (event.type === 'red_card') {
      if (isTeamA) baseState.redCardsA += 1
      else baseState.redCardsB += 1
    } else if (event.type === 'yellow_card') {
      if (isTeamA) baseState.yellowCardsA += 1
      else baseState.yellowCardsB += 1
    } else if (event.type === 'injury') {
      if (isTeamA) baseState.injuriesA += 1
      else baseState.injuriesB += 1
    } else if (event.type === 'shot_on_target') {
      if (isTeamA) baseState.shotsOnTargetA += 1
      else baseState.shotsOnTargetB += 1
    } else if (event.type === 'xg_chance') {
      if (isTeamA) baseState.xgA = Number((baseState.xgA + 0.3).toFixed(1))
      else baseState.xgB = Number((baseState.xgB + 0.3).toFixed(1))
    } else if (event.type === 'dangerous_attack') {
      if (isTeamA) baseState.dangerousAttacksA += 1
      else baseState.dangerousAttacksB += 1
    } else if (event.type === 'momentum') {
      latestMomentum = event.team
    }
  }

  baseState.minute = Math.max(Number(liveMatchState.value.minute) || 0, latestMinute)
  baseState.momentum = latestMomentum
  const possessionDiff = Math.min(Math.abs(baseState.dangerousAttacksA - baseState.dangerousAttacksB) * 2, 18)
  if (latestMomentum === 'team_a') {
    baseState.possessionA = 50 + possessionDiff
    baseState.possessionB = 50 - possessionDiff
  } else if (latestMomentum === 'team_b') {
    baseState.possessionA = 50 - possessionDiff
    baseState.possessionB = 50 + possessionDiff
  }

  liveMatchState.value = {
    ...baseState,
    notes: liveMatchState.value.notes
  }
}

const triggerLivePrediction = async () => {
  if (!canPredict.value) {
    return
  }
  await startLivePrediction({ silent: true, preserveResult: true })
}

const applyLiveEvent = async (type) => {
  const minute = Number(eventDraft.value.minute) || Number(liveMatchState.value.minute) || 0
  liveEvents.value.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    minute,
    team: eventDraft.value.team,
    type,
    description: eventDraft.value.description.trim(),
    createdAt: Date.now()
  })
  sortLiveEvents()
  syncLiveStateFromEvents()
  eventDraft.value.description = ''
  scheduleLivePrediction()
}

const removeLiveEvent = async (eventId) => {
  liveEvents.value = liveEvents.value.filter(event => event.id !== eventId)
  syncLiveStateFromEvents()
  scheduleLivePrediction()
}

const clearLiveEvents = async () => {
  liveEvents.value = []
  liveMatchState.value = {
    ...liveMatchState.value,
    scoreA: 0,
    scoreB: 0,
    redCardsA: 0,
    redCardsB: 0,
    yellowCardsA: 0,
    yellowCardsB: 0,
    shotsOnTargetA: 0,
    shotsOnTargetB: 0,
    xgA: 0,
    xgB: 0,
    dangerousAttacksA: 0,
    dangerousAttacksB: 0,
    injuriesA: 0,
    injuriesB: 0,
    possessionA: 50,
    possessionB: 50,
    momentum: 'balanced'
  }
  livePredictionResult.value = null
}

const normalizeSourceEvents = (events = []) => {
  const now = Date.now()
  return events.map((event, index) => ({
    id: event.id || `live-source-${now}-${index}`,
    minute: Number(event.minute) || 0,
    team: event.team || 'team_a',
    type: event.type || 'event',
    description: event.description || '',
    createdAt: now - index
  }))
}

const stopLiveSourceAutoSync = () => {
  liveSourceConfig.value.autoSync = false
  if (liveSourcePollTimer) {
    clearTimeout(liveSourcePollTimer)
    liveSourcePollTimer = null
  }
}

const scheduleLiveSourceAutoSync = () => {
  if (!liveSourceConfig.value.autoSync) {
    return
  }
  if (!liveSourceConfig.value.autoSelectCurrent && !liveSourceConfig.value.fixtureId) {
    return
  }
  if (liveSourcePollTimer) {
    clearTimeout(liveSourcePollTimer)
  }
  const delay = Math.max(Number(liveSourceConfig.value.pollSeconds) || 30, 15) * 1000
  liveSourcePollTimer = setTimeout(async () => {
    await syncLiveSourcePrediction({ silent: true })
    scheduleLiveSourceAutoSync()
  }, delay)
}

const fetchLiveSourceProviders = async () => {
  try {
    const res = await fetch('/api/predict/live-source/providers')
    const json = await res.json()
    if (json.success) {
      liveSourceProviders.value = json.data.providers || []
      const defaultProvider = json.data.default_provider
      if (defaultProvider) {
        liveSourceConfig.value.provider = defaultProvider
      }
      if (json.data.poll_interval_seconds) {
        liveSourceConfig.value.pollSeconds = Math.max(Number(json.data.poll_interval_seconds) || 30, 15)
      }
      const selectedProvider = (json.data.providers || []).find(provider => provider.id === liveSourceConfig.value.provider)
      if (selectedProvider?.recommended_poll_seconds) {
        liveSourceConfig.value.pollSeconds = Math.max(
          Number(liveSourceConfig.value.pollSeconds) || 30,
          Number(selectedProvider.recommended_poll_seconds) || 30
        )
      }
    }
  } catch (error) {
    console.error('Failed to fetch live source providers', error)
  }
}

const fetchLiveSourceMatches = async () => {
  isLoadingLiveMatches.value = true
  liveSourceStatus.value = ''
  try {
    const params = new URLSearchParams({
      provider: liveSourceConfig.value.provider,
      date: liveSourceConfig.value.date,
      live_only: String(liveSourceConfig.value.liveOnly)
    })
    const res = await fetch(`/api/predict/live-source/matches?${params.toString()}`)
    const json = await res.json()
    if (json.success) {
      liveSourceMatches.value = json.data.matches || []
      if (!liveSourceConfig.value.fixtureId && liveSourceMatches.value.length > 0) {
        liveSourceConfig.value.fixtureId = liveSourceMatches.value[0].fixture_id
      }
      liveSourceStatus.value = `已加载 ${liveSourceMatches.value.length} 场比赛`
    } else {
      liveSourceStatus.value = `加载失败：${json.error}`
    }
  } catch (error) {
    console.error('Failed to fetch live source matches', error)
    liveSourceStatus.value = '加载直播比赛列表失败'
  } finally {
    isLoadingLiveMatches.value = false
  }
}

const syncLiveSourcePrediction = async ({ silent = false } = {}) => {
  if (!liveSourceConfig.value.autoSelectCurrent && !liveSourceConfig.value.fixtureId) {
    if (!silent) {
      alert('请先选择一场直播比赛')
    }
    return
  }

  isSyncingLiveSource.value = true
  stopHistoricalReplayPlayback()
  try {
    const endpoint = liveSourceConfig.value.autoSelectCurrent
      ? '/api/predict/live-source/auto-analyze'
      : '/api/predict/live-source/analyze'
    const payload = liveSourceConfig.value.autoSelectCurrent
      ? {
          provider: liveSourceConfig.value.provider,
          teamA: matchConfig.value.teamA,
          teamB: matchConfig.value.teamB,
          date: liveSourceConfig.value.date,
          liveOnly: liveSourceConfig.value.liveOnly,
          factors: matchConfig.value.factors
        }
      : {
          provider: liveSourceConfig.value.provider,
          fixtureId: liveSourceConfig.value.fixtureId,
          factors: matchConfig.value.factors
        }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    const json = await res.json()
    if (json.success) {
      const payload = json.data || {}
      const match = payload.match || {}
      const providerState = match.live_state || {}
      suppressLocalAutoPredictUntil = Date.now() + 1200
      matchConfig.value.teamA = payload.team_a || matchConfig.value.teamA
      matchConfig.value.teamB = payload.team_b || matchConfig.value.teamB
      if (payload.matched_fixture?.fixture_id) {
        liveSourceConfig.value.fixtureId = payload.matched_fixture.fixture_id
      } else if (match.fixture_id) {
        liveSourceConfig.value.fixtureId = match.fixture_id
      }
      liveMatchState.value = {
        ...liveMatchState.value,
        ...providerState
      }
      liveEvents.value = normalizeSourceEvents(providerState.events || [])
      sortLiveEvents()
      livePredictionResult.value = payload.prediction || null
      liveSourceMeta.value = match
      liveSourceStatus.value = `最近同步：${new Date().toLocaleTimeString()}`
    } else if (!silent) {
      alert(`直播同步失败：${json.error}`)
    }
  } catch (error) {
    console.error('Failed to sync live source', error)
    if (!silent) {
      alert('同步真实直播数据失败')
    }
  } finally {
    isSyncingLiveSource.value = false
  }
}

const toggleLiveSourceAutoSync = async () => {
  if (liveSourceConfig.value.autoSync) {
    stopLiveSourceAutoSync()
    liveSourceStatus.value = '已停止自动直播同步'
    return
  }
  liveSourceConfig.value.autoSync = true
  await syncLiveSourcePrediction()
  scheduleLiveSourceAutoSync()
}

const clearHistoricalReplayTimer = () => {
  if (historicalReplayTimer) {
    clearTimeout(historicalReplayTimer)
    historicalReplayTimer = null
  }
}

const stopHistoricalReplayPlayback = () => {
  isHistoricalReplayPlaying.value = false
  clearHistoricalReplayTimer()
}

const fetchHistoricalReplays = async () => {
  try {
    const res = await fetch('/api/predict/historical-replays')
    const json = await res.json()
    if (json.success) {
      historicalReplays.value = json.data.replays || []
      if (!historicalReplayConfig.value.replayId && historicalReplays.value.length > 0) {
        historicalReplayConfig.value.replayId = historicalReplays.value[0].id
      }
    }
  } catch (error) {
    console.error('Failed to fetch historical replays', error)
  }
}

const loadHistoricalReplaySnapshot = async (cursor = 0, { silent = false } = {}) => {
  if (!historicalReplayConfig.value.replayId) {
    if (!silent) {
      alert('请先选择一场历史回放比赛')
    }
    return
  }

  isLoadingHistoricalReplay.value = true
  stopLiveSourceAutoSync()
  try {
    const res = await fetch('/api/predict/historical-replays/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        replayId: historicalReplayConfig.value.replayId,
        eventCursor: cursor,
        factors: matchConfig.value.factors
      })
    })
    const json = await res.json()
    if (json.success) {
      const payload = json.data || {}
      const replay = payload.replay || {}
      suppressLocalAutoPredictUntil = Date.now() + 1500
      matchConfig.value.teamA = payload.team_a || matchConfig.value.teamA
      matchConfig.value.teamB = payload.team_b || matchConfig.value.teamB
      liveMatchState.value = {
        ...liveMatchState.value,
        ...(payload.live_state || {})
      }
      liveEvents.value = normalizeSourceEvents(payload.applied_events || [])
      sortLiveEvents()
      livePredictionResult.value = payload.prediction || null
      historicalReplayMeta.value = replay
      historicalReplayCursor.value = payload.event_cursor || 0
      historicalReplayCurrentEvent.value = payload.current_event || null
      liveSourceMeta.value = null

      if (payload.current_event) {
        historicalReplayStatus.value = `已推进到第 ${payload.current_event.minute} 分钟：${payload.current_event.description}`
      } else {
        historicalReplayStatus.value = `已载入开场前状态，待推进 ${replay.event_count || 0} 个关键事件`
      }

      if ((payload.event_cursor || 0) >= (replay.event_count || 0)) {
        stopHistoricalReplayPlayback()
        historicalReplayStatus.value = `回放完成：${replay.final_score || ''}`
      }
    } else if (!silent) {
      alert(`载入历史回放失败：${json.error}`)
    }
  } catch (error) {
    console.error('Failed to load historical replay', error)
    if (!silent) {
      alert('载入历史回放失败')
    }
  } finally {
    isLoadingHistoricalReplay.value = false
  }
}

const scheduleHistoricalReplayTick = () => {
  clearHistoricalReplayTimer()
  if (!isHistoricalReplayPlaying.value || !historicalReplayMeta.value) {
    return
  }

  historicalReplayTimer = setTimeout(async () => {
    const total = historicalReplayMeta.value?.event_count || 0
    if (historicalReplayCursor.value >= total) {
      stopHistoricalReplayPlayback()
      historicalReplayStatus.value = `回放完成：${historicalReplayMeta.value?.final_score || ''}`
      return
    }
    await loadHistoricalReplaySnapshot(historicalReplayCursor.value + 1, { silent: true })
    if (isHistoricalReplayPlaying.value) {
      scheduleHistoricalReplayTick()
    }
  }, Math.max(Number(historicalReplayConfig.value.speedMs) || 2200, 800))
}

const toggleHistoricalReplayPlayback = async () => {
  if (isHistoricalReplayPlaying.value) {
    stopHistoricalReplayPlayback()
    historicalReplayStatus.value = '已暂停历史回放'
    return
  }

  if (!historicalReplayMeta.value || historicalReplayMeta.value.id !== historicalReplayConfig.value.replayId) {
    await loadHistoricalReplaySnapshot(0)
  }
  isHistoricalReplayPlaying.value = true
  historicalReplayStatus.value = '历史回放进行中...'
  scheduleHistoricalReplayTick()
}

const advanceHistoricalReplayStep = async () => {
  if (!historicalReplayConfig.value.replayId) {
    alert('请先选择一场历史回放比赛')
    return
  }
  stopHistoricalReplayPlayback()
  const nextCursor = historicalReplayMeta.value ? historicalReplayCursor.value + 1 : 0
  await loadHistoricalReplaySnapshot(nextCursor)
}

const resetHistoricalReplay = async () => {
  stopHistoricalReplayPlayback()
  await loadHistoricalReplaySnapshot(0)
}

// 获取已入库的球队
const fetchTeams = async () => {
  try {
    const res = await fetch('/api/predict/teams?scope=world_cup_2026')
    const json = await res.json()
    if (json.success) {
      availableTeams.value = json.data.teams
    }
  } catch (error) {
    console.error('Failed to fetch teams', error)
  }
}

// 处理文件上传
const handleFiles = async (files) => {
  for (const file of files) {
    const formData = new FormData()
    formData.append('file', file)
    try {
      await fetch('/api/predict/upload', {
        method: 'POST',
        body: formData
      })
    } catch (error) {
      console.error(`上传文件 ${file.name} 失败`, error)
    }
  }
  await fetchTeams()
}

// 同步 FIFA 官方球队数据
const syncFifaTeams = async () => {
  isSyncingFifa.value = true
  try {
    const res = await fetch('/api/predict/sync-fifa', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        scope: 'world_cup_2026'
      })
    })
    const json = await res.json()
    if (json.success) {
      const { synced_count, failed_count } = json.data
      alert(`世界杯48队数据同步完成：成功 ${synced_count} 支，失败 ${failed_count} 支`)
      await fetchTeams()
    } else {
      alert('FIFA 数据同步失败：' + json.error)
    }
  } catch (error) {
    console.error('Sync FIFA teams error', error)
    alert('同步 FIFA 数据时发生网络或服务错误')
  } finally {
    isSyncingFifa.value = false
  }
}

const handleFileSelect = (e) => {
  handleFiles(Array.from(e.target.files))
}

const handleDrop = (e) => {
  isDragOver.value = false
  handleFiles(Array.from(e.dataTransfer.files))
}

// 发起预测
const startPrediction = async () => {
  isPredicting.value = true
  predictionResult.value = null
  
  try {
    const res = await fetch('/api/predict/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(matchConfig.value)
    })
    
    const json = await res.json()
    if (json.success) {
      // json.data 可能是 JSON 字符串也可能是对象
      let dataObj = json.data
      if (typeof dataObj === 'string') {
        // 部分模型外层可能包了字符串
        dataObj = JSON.parse(dataObj)
      }
      predictionResult.value = dataObj
    } else {
      alert('预测失败：' + json.error)
    }
  } catch (error) {
    console.error('Prediction error', error)
    alert('网络或服务错误')
  } finally {
    isPredicting.value = false
  }
}

const startLivePrediction = async ({ silent = false, preserveResult = false } = {}) => {
  isLivePredicting.value = true
  if (!preserveResult) {
    livePredictionResult.value = null
  }

  try {
    const res = await fetch('/api/predict/live-analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        teamA: matchConfig.value.teamA,
        teamB: matchConfig.value.teamB,
        factors: matchConfig.value.factors,
        liveState: {
          ...liveMatchState.value,
          events: liveEvents.value
        }
      })
    })

    const json = await res.json()
    if (json.success) {
      let dataObj = json.data
      if (typeof dataObj === 'string') {
        dataObj = JSON.parse(dataObj)
      }
      livePredictionResult.value = dataObj
    } else {
      if (!silent) {
        alert('动态预测失败：' + json.error)
      }
    }
  } catch (error) {
    console.error('Live prediction error', error)
    if (!silent) {
      alert('动态预测时发生网络或服务错误')
    }
  } finally {
    isLivePredicting.value = false
  }
}

const scheduleLivePrediction = () => {
  if (!canPredict.value) {
    return
  }
  if (Date.now() < suppressLocalAutoPredictUntil) {
    return
  }
  if (liveAutoTimer) {
    clearTimeout(liveAutoTimer)
  }
  liveAutoTimer = setTimeout(() => {
    triggerLivePrediction()
  }, 450)
}

watch(
  () => [
    matchConfig.value.teamA,
    matchConfig.value.teamB,
    liveMatchState.value.minute,
    liveMatchState.value.scoreA,
    liveMatchState.value.scoreB,
    liveMatchState.value.redCardsA,
    liveMatchState.value.redCardsB,
    liveMatchState.value.yellowCardsA,
    liveMatchState.value.yellowCardsB,
    liveMatchState.value.possessionA,
    liveMatchState.value.possessionB,
    liveMatchState.value.shotsOnTargetA,
    liveMatchState.value.shotsOnTargetB,
    liveMatchState.value.xgA,
    liveMatchState.value.xgB,
    liveMatchState.value.dangerousAttacksA,
    liveMatchState.value.dangerousAttacksB,
    liveMatchState.value.injuriesA,
    liveMatchState.value.injuriesB,
    liveMatchState.value.momentum,
    liveMatchState.value.notes
  ],
  () => {
    if (liveSourceConfig.value.autoSync && (liveSourceConfig.value.autoSelectCurrent || liveSourceConfig.value.fixtureId)) {
      return
    }
    if (livePredictionResult.value || liveEvents.value.length > 0) {
      scheduleLivePrediction()
    }
  }
)

watch(
  () => [matchConfig.value.teamA, matchConfig.value.teamB],
  () => {
    liveEvents.value = []
    livePredictionResult.value = null
    liveSourceMeta.value = null
    historicalReplayMeta.value = null
    historicalReplayCurrentEvent.value = null
    historicalReplayCursor.value = 0
    stopHistoricalReplayPlayback()
  }
)

watch(
  () => [liveSourceConfig.value.provider, liveSourceConfig.value.date, liveSourceConfig.value.liveOnly, liveSourceConfig.value.autoSelectCurrent],
  () => {
    liveSourceMatches.value = []
    liveSourceConfig.value.fixtureId = ''
    stopLiveSourceAutoSync()
  }
)

onMounted(() => {
  fetchTeams()
  fetchLiveSourceProviders()
  fetchHistoricalReplays()
})

onBeforeUnmount(() => {
  if (liveAutoTimer) {
    clearTimeout(liveAutoTimer)
  }
  if (liveSourcePollTimer) {
    clearTimeout(liveSourcePollTimer)
  }
  clearHistoricalReplayTimer()
})
</script>

<style scoped>
.predict-container {
  min-height: 100vh;
  position: relative;
  background-color: #1b6f2f;
  background-image: url('../assets/stadium_photo.png');
  background-repeat: no-repeat;
  background-position: center bottom;
  background-size: cover;
  background-attachment: fixed;
  font-family: 'Noto Sans SC', sans-serif;
  color: #333;
}

.predict-container::before {
  content: '';
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.22);
  pointer-events: none;
  z-index: 0;
}

.navbar {
  position: relative;
  z-index: 1;
  height: 60px;
  background: #1a365d;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.nav-brand {
  font-size: 1.2rem;
  font-weight: bold;
  letter-spacing: 1px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-btn {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.95rem;
}

.nav-btn:hover {
  background: rgba(255,255,255,0.2);
}

.main-content {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.page-title {
  text-align: center;
  font-size: 2.5rem;
  color: #1a365d;
  margin-bottom: 10px;
}

.page-desc {
  text-align: center;
  color: #666;
  margin-bottom: 40px;
}

.dashboard {
  display: flex;
  gap: 30px;
  margin-bottom: 40px;
}

.panel {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(8px);
}

.left-panel {
  flex: 1;
}

.right-panel {
  flex: 1.5;
}

.panel-title {
  font-size: 1.3rem;
  margin-bottom: 20px;
  color: #2c3e50;
  border-bottom: 2px solid #edf2f7;
  padding-bottom: 10px;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed #cbd5e0;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f8fafc;
  margin-bottom: 20px;
}

.upload-zone:hover, .upload-zone.drag-over {
  border-color: #3182ce;
  background: #ebf8ff;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 10px;
}

.upload-hint {
  font-size: 0.8rem;
  color: #a0aec0;
}

.sync-btn {
  width: 100%;
  padding: 12px 16px;
  background: #1a365d;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 8px;
  transition: background 0.2s;
}

.sync-btn:hover:not(:disabled) {
  background: #2b4f7a;
}

.sync-btn:disabled {
  background: #a0aec0;
  cursor: not-allowed;
}

.sync-hint {
  font-size: 0.82rem;
  color: #718096;
  line-height: 1.5;
  margin-bottom: 20px;
}

/* Teams Grid */
.teams-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 15px;
}

.team-tag {
  background: #e2e8f0;
  color: #2d3748;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}

.empty-hint {
  color: #a0aec0;
  font-size: 0.9rem;
  margin-top: 15px;
}

/* Match Setup */
.team-select-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 20px;
}

.select-box {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.select-box label {
  font-weight: bold;
  margin-bottom: 8px;
  color: #4a5568;
}

.select-box select {
  padding: 12px;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 1rem;
  outline: none;
}

.vs-badge {
  font-size: 1.5rem;
  font-weight: 900;
  color: #e53e3e;
  padding-top: 25px;
}

.factors-input {
  display: flex;
  flex-direction: column;
  margin-bottom: 25px;
}

.factors-input label {
  font-weight: bold;
  margin-bottom: 8px;
  color: #4a5568;
}

.factors-input textarea {
  padding: 12px;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 1rem;
  outline: none;
  resize: vertical;
}

.predict-btn {
  width: 100%;
  padding: 16px;
  background: #3182ce;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.predict-btn:hover:not(:disabled) {
  background: #2b6cb0;
}

.predict-btn:disabled {
  background: #a0aec0;
  cursor: not-allowed;
}

.live-mode-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #cbd5e0, transparent);
  margin: 28px 0 24px;
}

.live-panel {
  background: #f8fbff;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  padding: 20px;
}

.sub-panel-title {
  margin: 0 0 10px;
  color: #1a365d;
}

.live-hint {
  margin: 0 0 18px;
  color: #4a5568;
  line-height: 1.6;
  font-size: 0.92rem;
}

.source-panel {
  margin-bottom: 18px;
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dbeafe;
  border-radius: 12px;
}

.source-notice {
  margin-bottom: 16px;
  padding: 12px 14px;
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-radius: 10px;
  color: #9a3412;
  line-height: 1.6;
  font-size: 0.92rem;
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px 16px;
  margin-bottom: 16px;
}

.source-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.source-btn {
  background: #dbeafe;
  color: #1e40af;
}

.source-btn:hover:not(:disabled) {
  background: #bfdbfe;
}

.fixture-select {
  margin-bottom: 12px;
}

.source-status {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #edf2f7;
  color: #2d3748;
  font-size: 0.92rem;
}

.source-meta {
  margin-top: 14px;
  justify-content: flex-start;
}

.replay-panel {
  margin-bottom: 18px;
}

.replay-grid {
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
}

.replay-btn {
  background: #ede9fe;
  color: #5b21b6;
}

.replay-btn:hover:not(:disabled) {
  background: #ddd6fe;
}

.replay-current-event {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e3a8a;
  line-height: 1.6;
  font-size: 0.92rem;
}

.live-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 16px;
  margin-bottom: 18px;
}

.live-field {
  display: flex;
  flex-direction: column;
}

.live-field label {
  font-weight: bold;
  margin-bottom: 8px;
  color: #4a5568;
}

.live-field input,
.live-field select {
  padding: 12px;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 1rem;
  outline: none;
  background: #fff;
}

.live-btn {
  background: #2f855a;
}

.live-btn:hover:not(:disabled) {
  background: #276749;
}

.event-composer {
  margin: 10px 0 20px;
  padding: 18px;
  background: #ffffff;
  border: 1px solid #dbeafe;
  border-radius: 12px;
}

.event-title {
  margin: 0 0 8px;
  color: #1a365d;
}

.event-hint {
  margin: 0 0 16px;
  color: #4a5568;
  line-height: 1.6;
  font-size: 0.9rem;
}

.event-toolbar {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px 16px;
  margin-bottom: 16px;
}

.event-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
}

.event-btn,
.ghost-btn {
  border: none;
  border-radius: 999px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: transform 0.15s ease, opacity 0.2s ease, background 0.2s ease;
}

.event-btn:hover:not(:disabled),
.ghost-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.event-btn:disabled,
.ghost-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.event-btn.goal { background: #c6f6d5; color: #22543d; }
.event-btn.red { background: #fed7d7; color: #742a2a; }
.event-btn.yellow { background: #faf089; color: #744210; }
.event-btn.injury { background: #feebc8; color: #7b341e; }
.event-btn.shot { background: #bee3f8; color: #2a4365; }
.event-btn.chance { background: #d6bcfa; color: #44337a; }
.event-btn.danger { background: #fbb6ce; color: #702459; }
.event-btn.momentum { background: #e9d8fd; color: #553c9a; }

.ghost-btn {
  background: #edf2f7;
  color: #2d3748;
}

.timeline-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
}

.timeline-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.timeline-empty {
  color: #718096;
  line-height: 1.6;
}

.timeline-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.timeline-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
}

.timeline-minute {
  font-size: 0.85rem;
  color: #718096;
  margin-bottom: 4px;
}

.timeline-text {
  color: #2d3748;
  line-height: 1.5;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Result Section */
.result-section {
  background: #fff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.result-title {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
}

/* Win Rate Bars */
.win-rate-bars {
  display: flex;
  height: 40px;
  border-radius: 20px;
  overflow: hidden;
  margin-bottom: 30px;
  box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
}

.rate-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
  font-size: 0.9rem;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  overflow: hidden;
}

.rate-bar.team-a { background: #3182ce; }
.rate-bar.draw { background: #a0aec0; }
.rate-bar.team-b { background: #e53e3e; }

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.analysis-card {
  background: #f8fafc;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.analysis-card h3 {
  color: #2b6cb0;
  margin-bottom: 15px;
}

.analysis-card p {
  line-height: 1.6;
}

.analysis-card ul {
  padding-left: 20px;
  line-height: 1.6;
}

.live-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
  justify-content: center;
}

.meta-chip {
  background: #edf2f7;
  color: #2d3748;
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 0.92rem;
  font-weight: 600;
}

.delta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.delta-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 18px;
  text-align: center;
}

.delta-card h3 {
  margin: 0 0 10px;
  color: #2b6cb0;
  font-size: 1rem;
}

.delta-card p {
  margin: 0 0 8px;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a365d;
}

.delta-card span {
  color: #718096;
  font-size: 0.88rem;
}

.recent-events-card {
  margin-bottom: 20px;
}

.final-verdict {
  background: #ebf8ff;
  padding: 20px;
  border-radius: 8px;
  border-left: 5px solid #3182ce;
  text-align: center;
}

.verdict-text {
  font-size: 1.2rem;
  font-weight: bold;
  color: #2c3e50;
  margin-top: 10px;
}

@media (max-width: 960px) {
  .dashboard {
    flex-direction: column;
  }

  .analysis-grid,
  .delta-grid,
  .live-grid,
  .event-toolbar,
  .source-grid,
  .replay-grid {
    grid-template-columns: 1fr;
  }

  .source-actions,
  .event-actions,
  .timeline-head,
  .timeline-item {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

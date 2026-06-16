<template>
  <div class="team-detail-container">
    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <div class="nav-brand" @click="$router.push('/')" style="cursor: pointer;">
        🏆 返回预测中心
      </div>
      <div class="nav-links">
        <span class="version-text">球队图谱档案馆</span>
      </div>
    </nav>

    <div class="main-content">
      <div class="layout-container">
        
        <!-- 左侧：球队列表 -->
        <div class="sidebar">
          <h2 class="sidebar-title">球队名录</h2>
          <div class="team-list">
            <div 
              v-for="team in availableTeams" 
              :key="team" 
              class="team-item"
              :class="{ active: currentTeam === team }"
              @click="selectTeam(team)"
            >
              {{ team }}
            </div>
            <div v-if="availableTeams.length === 0" class="empty-hint">暂无球队数据</div>
          </div>
        </div>

        <!-- 右侧：图谱详情展示区 -->
        <div class="content-area">
          <div v-if="!currentTeam" class="empty-state">
            <div class="icon">👈</div>
            <h2>请在左侧选择一支球队</h2>
            <p>查看该球队由 AI 自动构建的专属知识图谱</p>
          </div>

          <div v-else-if="isLoading" class="loading-state">
            <div class="spinner"></div>
            <p>正在从 Zep 图谱库中提取【{{ currentTeam }}】的深度档案...</p>
          </div>

          <div v-else-if="error" class="error-state">
            <h2>出错了</h2>
            <p>{{ error }}</p>
            <button @click="loadTeamDetail(currentTeam)" class="retry-btn">重试</button>
          </div>

          <div v-else class="graph-detail">
            <h1 class="team-title">【{{ currentTeam }}】 知识图谱档案</h1>

            <!-- 核心节点 (Nodes) -->
            <div class="section-card" v-if="graphData?.nodes?.length">
              <h3 class="section-title">🧠 核心关联实体 (Nodes)</h3>
              <div class="nodes-grid">
                <div v-for="node in graphData.nodes" :key="node.uuid" class="node-card">
                  <div class="node-header">
                    <span class="node-name">{{ node.name }}</span>
                    <span class="node-label">{{ node.labels?.[0] || '实体' }}</span>
                  </div>
                  <p class="node-summary">{{ node.summary }}</p>
                </div>
              </div>
            </div>

            <!-- 关系链 (Edges) -->
            <div class="section-card" v-if="graphData?.edges?.length">
              <h3 class="section-title">🔗 深度关系链 (Edges)</h3>
              <div class="edges-list">
                <div v-for="(edge, index) in graphData.edges" :key="index" class="edge-item">
                  <div class="edge-relation">
                    <span class="badge">{{ edge.name }}</span>
                  </div>
                  <div class="edge-fact">{{ edge.fact }}</div>
                </div>
              </div>
            </div>

            <!-- 提取事实 (Facts) -->
            <div class="section-card" v-if="graphData?.facts?.length">
              <h3 class="section-title">📌 关键事实摘要 (Facts)</h3>
              <ul class="facts-list">
                <li v-for="(fact, index) in graphData.facts" :key="index">
                  {{ fact }}
                </li>
              </ul>
            </div>

            <div class="section-card" v-if="structuredText">
              <h3 class="section-title">📊 结构化球队档案</h3>
              <div class="raw-text">
                {{ structuredText }}
              </div>
              <div v-if="graphSeeded" class="empty-hint" style="margin-top: 12px;">
                已触发该球队图谱构建，请稍等片刻后刷新查看 Nodes/Edges/Facts。
              </div>
            </div>

            <!-- 本地背景兜底 -->
            <div class="section-card" v-if="localText">
              <h3 class="section-title">📄 原始档案文件</h3>
              <div class="raw-text">
                {{ localText }}
              </div>
            </div>
            
            <div v-if="!graphData?.nodes?.length && !graphData?.edges?.length && !localText" class="empty-hint" style="margin-top: 40px;">
              该球队暂无详细的图谱数据，可能后台仍在构建中...
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const availableTeams = ref([])
const currentTeam = ref('')
const isLoading = ref(false)
const error = ref('')
const graphData = ref(null)
const localText = ref('')
const structuredText = ref('')
const graphSeeded = ref(false)

// 获取所有球队
const fetchTeams = async () => {
  try {
    const res = await fetch('/api/predict/teams?scope=world_cup_2026')
    const json = await res.json()
    if (json.success) {
      availableTeams.value = json.data.teams
    }
  } catch (err) {
    console.error('Failed to fetch teams', err)
  }
}

// 选择球队并加载图谱数据
const selectTeam = (team) => {
  currentTeam.value = team
  loadTeamDetail(team)
}

// 加载球队图谱详情
const loadTeamDetail = async (team) => {
  isLoading.value = true
  error.value = ''
  graphData.value = null
  localText.value = ''
  structuredText.value = ''
  graphSeeded.value = false
  
  try {
    const res = await fetch(`/api/predict/team/${encodeURIComponent(team)}`)
    const json = await res.json()
    if (json.success) {
      graphData.value = json.data.graph_data
      localText.value = json.data.local_text
      structuredText.value = json.data.structured_text || ''
      graphSeeded.value = !!json.data.graph_seeded
    } else {
      error.value = json.error || '加载图谱数据失败'
    }
  } catch (err) {
    console.error('Fetch graph error', err)
    error.value = '网络或服务错误'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchTeams()
})
</script>

<style scoped>
.team-detail-container {
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

.team-detail-container::before {
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

.main-content {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px 20px;
}

.layout-container {
  display: flex;
  gap: 24px;
  height: calc(100vh - 120px);
}

/* 侧边栏 */
.sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-title {
  padding: 20px;
  margin: 0;
  font-size: 1.2rem;
  color: #2c3e50;
  border-bottom: 1px solid #edf2f7;
  background: #f8fafc;
}

.team-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.team-item {
  padding: 15px 20px;
  cursor: pointer;
  border-left: 4px solid transparent;
  transition: all 0.2s;
  font-size: 1.05rem;
  color: #4a5568;
}

.team-item:hover {
  background: #f7fafc;
  color: #2b6cb0;
}

.team-item.active {
  background: #ebf8ff;
  border-left-color: #3182ce;
  color: #2b6cb0;
  font-weight: bold;
}

/* 右侧内容区 */
.content-area {
  flex: 1;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(8px);
  overflow-y: auto;
  padding: 30px;
  position: relative;
}

.empty-state, .loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #718096;
  text-align: center;
}

.empty-state .icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3182ce;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.team-title {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 30px;
  border-bottom: 2px solid #edf2f7;
  padding-bottom: 15px;
}

.section-card {
  margin-bottom: 30px;
  background: #f8fafc;
  border-radius: 10px;
  padding: 20px;
  border: 1px solid #e2e8f0;
}

.section-title {
  font-size: 1.2rem;
  color: #2d3748;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 节点样式 */
.nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
}

.node-card {
  background: #fff;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  border-left: 4px solid #4299e1;
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.node-name {
  font-weight: bold;
  color: #2b6cb0;
  font-size: 1.1rem;
}

.node-label {
  font-size: 0.8rem;
  background: #edf2f7;
  padding: 2px 8px;
  border-radius: 12px;
  color: #4a5568;
}

.node-summary {
  font-size: 0.95rem;
  color: #4a5568;
  line-height: 1.5;
  margin: 0;
}

/* 关系链样式 */
.edges-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edge-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  background: #fff;
  padding: 12px 15px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.edge-relation .badge {
  background: #ecc94b;
  color: #744210;
  font-size: 0.85rem;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: bold;
  white-space: nowrap;
}

.edge-fact {
  color: #2d3748;
  line-height: 1.5;
}

/* 事实列表 */
.facts-list {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.facts-list li {
  position: relative;
  padding-left: 20px;
  margin-bottom: 10px;
  color: #4a5568;
  line-height: 1.6;
}

.facts-list li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #4299e1;
  font-weight: bold;
}

/* 原始文本 */
.raw-text {
  white-space: pre-wrap;
  font-family: monospace;
  background: #fff;
  padding: 15px;
  border-radius: 8px;
  color: #4a5568;
  font-size: 0.95rem;
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
}

.retry-btn {
  margin-top: 20px;
  padding: 10px 24px;
  background: #3182ce;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
}

.retry-btn:hover {
  background: #2b6cb0;
}

.empty-hint {
  text-align: center;
  color: #a0aec0;
  padding: 20px;
}
</style>

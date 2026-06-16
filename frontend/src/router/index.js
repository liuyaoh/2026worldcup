import { createRouter, createWebHistory } from 'vue-router'
import PredictView from '../views/PredictView.vue'
import TeamDetailView from '../views/TeamDetailView.vue'

const routes = [
  {
    path: '/',
    name: 'PredictView',
    component: PredictView
  },
  {
    path: '/team-detail',
    name: 'TeamDetail',
    component: TeamDetailView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

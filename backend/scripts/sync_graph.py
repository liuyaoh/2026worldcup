import os
import sys

# 将 backend 目录加入路径以便导入内部模块
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, backend_dir)

from app.api.predict import get_world_cup_graph_id, async_add_to_graph, TEAMS_DIR
from app.utils.logger import get_logger

logger = get_logger('world_cup.scripts.sync_graph')

def sync_existing_teams():
    logger.info("开始同步历史球队数据到 Zep 图谱...")
    
    graph_id = get_world_cup_graph_id()
    if not graph_id:
        logger.error("无法获取或创建世界杯图谱")
        return
        
    logger.info(f"目标图谱 ID: {graph_id}")
    
    synced_count = 0
    if os.path.exists(TEAMS_DIR):
        for filename in os.listdir(TEAMS_DIR):
            if filename.endswith('.txt') and not filename.startswith('temp_'):
                file_path = os.path.join(TEAMS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if content.strip():
                        logger.info(f"正在将 [{filename}] 加入图谱...")
                        async_add_to_graph(graph_id, content)
                        synced_count += 1
                except Exception as e:
                    logger.error(f"处理文件 {filename} 失败: {e}")
                    
    logger.info(f"同步任务分发完毕！共处理了 {synced_count} 个球队文件。")
    logger.info("请注意：Zep 图谱在后台构建可能需要几十秒的时间，请稍后在前端刷新查看。")

if __name__ == '__main__':
    sync_existing_teams()

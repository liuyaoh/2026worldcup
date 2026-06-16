import os
import sys

# 直接引入 app/services，避免触发 Flask 应用初始化
services_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../app"))
sys.path.insert(0, services_root)

from services.fifa_team_sync import FifaTeamSyncService


def main() -> None:
    result = FifaTeamSyncService.sync_teams(scope="world_cup_2026")
    print("FIFA 球队数据同步完成")
    print(f"- 请求数量: {result['requested_count']}")
    print(f"- 成功数量: {result['synced_count']}")
    print(f"- 失败数量: {result['failed_count']}")
    if result["failed"]:
        print("- 失败详情:")
        for item in result["failed"]:
            print(f"  - {item['name']} ({item['fifa_code']}): {item['error']}")


if __name__ == "__main__":
    main()

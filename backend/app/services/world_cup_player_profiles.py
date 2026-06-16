import json
import os

from ..utils.llm_client import LLMClient
from .world_cup_squad_profiles import WORLD_CUP_2026_SQUAD_PROFILES


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
TEAM_DATA_DIR = os.path.join(BASE_DIR, "data", "teams")
KEY_PLAYER_CACHE_FILE = os.path.join(TEAM_DATA_DIR, "world_cup_key_players.json")


class WorldCupPlayerProfileService:
    @classmethod
    def _load_cache(cls) -> dict:
        if not os.path.exists(KEY_PLAYER_CACHE_FILE):
            return {}
        try:
            with open(KEY_PLAYER_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def _save_cache(cls, data: dict) -> None:
        os.makedirs(TEAM_DATA_DIR, exist_ok=True)
        with open(KEY_PLAYER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def get_key_players(cls, fifa_code: str, team_name: str) -> list[dict]:
        if not fifa_code:
            return []

        cache = cls._load_cache()
        cached = cache.get(fifa_code)
        if isinstance(cached, list):
            return cached

        summary = (WORLD_CUP_2026_SQUAD_PROFILES.get(fifa_code) or {}).get("summary_cn")
        if not summary:
            return []

        try:
            llm = LLMClient()
            prompt = (
                f"请仅根据下面这段世界杯球队官方摘要，提取文中明确提到的球员，不要编造未出现的人名。\n"
                f"球队：{team_name}\n"
                f"摘要：{summary}\n\n"
                "请返回 JSON，格式为："
                '{"players":[{"name":"球员名","role":"位置/角色","style_traits":["特点1","特点2"],"style_summary":"一句中文风格描述"}]}。\n'
                "要求：\n"
                "1. 只提取摘要里明确出现的球员。\n"
                "2. role 用简洁中文，如 门将/中卫/边锋/前锋/中场核心/边后卫。\n"
                "3. style_traits 给 2-4 个短中文标签。\n"
                "4. style_summary 用一句自然中文总结该球员风格。\n"
                "5. 如果摘要里没有明确风格词，可以根据摘要里的角色定位做保守概括，但不要夸张。"
            )
            result = llm.chat_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            players = result.get("players") or []
            normalized = []
            for item in players:
                name = (item.get("name") or "").strip()
                if not name:
                    continue
                normalized.append(
                    {
                        "name": name,
                        "role": (item.get("role") or "").strip(),
                        "style_traits": [str(x).strip() for x in (item.get("style_traits") or []) if str(x).strip()],
                        "style_summary": (item.get("style_summary") or "").strip(),
                    }
                )
            cache[fifa_code] = normalized
            cls._save_cache(cache)
            return normalized
        except Exception:
            return []

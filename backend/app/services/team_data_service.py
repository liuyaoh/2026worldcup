import json
import os
from datetime import datetime, timezone
from typing import Any

from .world_cup_player_profiles import WorldCupPlayerProfileService
from .world_cup_squad_profiles import WORLD_CUP_2026_SQUAD_PROFILES


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
TEAM_DATA_DIR = os.path.join(BASE_DIR, "data", "teams")
TEAM_DATA_FILE = os.path.join(TEAM_DATA_DIR, "fifa_teams.json")


DEFAULT_TEAM_REGISTRY = [
    {"fifa_code": "ARG", "name_cn": "阿根廷", "name_en": "Argentina", "aliases": ["Argentina", "阿根廷国家队"]},
    {"fifa_code": "FRA", "name_cn": "法国", "name_en": "France", "aliases": ["France", "法国国家队"]},
    {"fifa_code": "ESP", "name_cn": "西班牙", "name_en": "Spain", "aliases": ["Spain", "西班牙国家队"]},
    {"fifa_code": "ENG", "name_cn": "英格兰", "name_en": "England", "aliases": ["England", "英格兰国家队"]},
    {"fifa_code": "POR", "name_cn": "葡萄牙", "name_en": "Portugal", "aliases": ["Portugal", "葡萄牙国家队"]},
    {"fifa_code": "BRA", "name_cn": "巴西", "name_en": "Brazil", "aliases": ["Brazil", "巴西国家队"]},
    {"fifa_code": "NED", "name_cn": "荷兰", "name_en": "Netherlands", "aliases": ["Netherlands", "荷兰国家队"]},
    {"fifa_code": "MAR", "name_cn": "摩洛哥", "name_en": "Morocco", "aliases": ["Morocco", "摩洛哥国家队"]},
    {"fifa_code": "BEL", "name_cn": "比利时", "name_en": "Belgium", "aliases": ["Belgium", "比利时国家队"]},
    {"fifa_code": "GER", "name_cn": "德国", "name_en": "Germany", "aliases": ["Germany", "德国国家队"]},
    {"fifa_code": "USA", "name_cn": "美国", "name_en": "USA", "aliases": ["United States", "USA", "美国国家队", "美国"]},
    {"fifa_code": "MEX", "name_cn": "墨西哥", "name_en": "Mexico", "aliases": ["Mexico", "墨西哥国家队"]},
    {"fifa_code": "JPN", "name_cn": "日本", "name_en": "Japan", "aliases": ["Japan", "日本国家队"]},
    {"fifa_code": "URU", "name_cn": "乌拉圭", "name_en": "Uruguay", "aliases": ["Uruguay", "乌拉圭国家队"]},
    {"fifa_code": "CRO", "name_cn": "克罗地亚", "name_en": "Croatia", "aliases": ["Croatia", "克罗地亚国家队"]},
    {"fifa_code": "COL", "name_cn": "哥伦比亚", "name_en": "Colombia", "aliases": ["Colombia", "哥伦比亚国家队"]},
    {"fifa_code": "ITA", "name_cn": "意大利", "name_en": "Italy", "aliases": ["Italy", "意大利国家队"]},
    {"fifa_code": "SUI", "name_cn": "瑞士", "name_en": "Switzerland", "aliases": ["Switzerland", "瑞士国家队"]},
    {"fifa_code": "DEN", "name_cn": "丹麦", "name_en": "Denmark", "aliases": ["Denmark", "丹麦国家队"]},
    {"fifa_code": "SEN", "name_cn": "塞内加尔", "name_en": "Senegal", "aliases": ["Senegal", "塞内加尔国家队"]},
    {"fifa_code": "KOR", "name_cn": "韩国", "name_en": "Korea Republic", "aliases": ["South Korea", "Korea Republic", "韩国国家队", "韩国"]},
    {"fifa_code": "CAN", "name_cn": "加拿大", "name_en": "Canada", "aliases": ["Canada", "加拿大国家队"]},
    {"fifa_code": "AUS", "name_cn": "澳大利亚", "name_en": "Australia", "aliases": ["Australia", "澳大利亚国家队"]},
    {"fifa_code": "IRN", "name_cn": "伊朗", "name_en": "IR Iran", "aliases": ["Iran", "IR Iran", "伊朗国家队", "伊朗"]},
    {"fifa_code": "ECU", "name_cn": "厄瓜多尔", "name_en": "Ecuador", "aliases": ["Ecuador", "厄瓜多尔国家队"]},
]

WORLD_CUP_2026_REGISTRY = [
    {"fifa_code": "MEX", "name_cn": "墨西哥", "name_en": "Mexico", "aliases": ["Mexico", "墨西哥国家队"], "group": "A"},
    {"fifa_code": "RSA", "name_cn": "南非", "name_en": "South Africa", "aliases": ["South Africa", "南非国家队"], "group": "A"},
    {"fifa_code": "KOR", "name_cn": "韩国", "name_en": "Korea Republic", "aliases": ["Korea Republic", "South Korea", "韩国国家队", "韩国"], "group": "A"},
    {"fifa_code": "CZE", "name_cn": "捷克", "name_en": "Czechia", "aliases": ["Czechia", "Czech Republic", "捷克国家队"], "group": "A"},
    {"fifa_code": "CAN", "name_cn": "加拿大", "name_en": "Canada", "aliases": ["Canada", "加拿大国家队"], "group": "B"},
    {"fifa_code": "BIH", "name_cn": "波黑", "name_en": "Bosnia and Herzegovina", "aliases": ["Bosnia and Herzegovina", "Bosnia-Herzegovina", "波黑国家队"], "group": "B"},
    {"fifa_code": "QAT", "name_cn": "卡塔尔", "name_en": "Qatar", "aliases": ["Qatar", "卡塔尔国家队"], "group": "B"},
    {"fifa_code": "SUI", "name_cn": "瑞士", "name_en": "Switzerland", "aliases": ["Switzerland", "瑞士国家队"], "group": "B"},
    {"fifa_code": "BRA", "name_cn": "巴西", "name_en": "Brazil", "aliases": ["Brazil", "巴西国家队"], "group": "C"},
    {"fifa_code": "MAR", "name_cn": "摩洛哥", "name_en": "Morocco", "aliases": ["Morocco", "摩洛哥国家队"], "group": "C"},
    {"fifa_code": "HAI", "name_cn": "海地", "name_en": "Haiti", "aliases": ["Haiti", "海地国家队"], "group": "C"},
    {"fifa_code": "SCO", "name_cn": "苏格兰", "name_en": "Scotland", "aliases": ["Scotland", "苏格兰国家队"], "group": "C"},
    {"fifa_code": "USA", "name_cn": "美国", "name_en": "USA", "aliases": ["USA", "United States", "美国国家队", "美国"], "group": "D"},
    {"fifa_code": "PAR", "name_cn": "巴拉圭", "name_en": "Paraguay", "aliases": ["Paraguay", "巴拉圭国家队"], "group": "D"},
    {"fifa_code": "AUS", "name_cn": "澳大利亚", "name_en": "Australia", "aliases": ["Australia", "澳大利亚国家队"], "group": "D"},
    {"fifa_code": "TUR", "name_cn": "土耳其", "name_en": "Turkiye", "aliases": ["Turkiye", "Türkiye", "Turkey", "土耳其国家队"], "group": "D"},
    {"fifa_code": "GER", "name_cn": "德国", "name_en": "Germany", "aliases": ["Germany", "德国国家队"], "group": "E"},
    {"fifa_code": "CUW", "name_cn": "库拉索", "name_en": "Curacao", "aliases": ["Curacao", "Curaçao", "库拉索国家队"], "group": "E"},
    {"fifa_code": "CIV", "name_cn": "科特迪瓦", "name_en": "Cote d'Ivoire", "aliases": ["Cote d'Ivoire", "Côte d'Ivoire", "Ivory Coast", "科特迪瓦国家队"], "group": "E"},
    {"fifa_code": "ECU", "name_cn": "厄瓜多尔", "name_en": "Ecuador", "aliases": ["Ecuador", "厄瓜多尔国家队"], "group": "E"},
    {"fifa_code": "NED", "name_cn": "荷兰", "name_en": "Netherlands", "aliases": ["Netherlands", "荷兰国家队"], "group": "F"},
    {"fifa_code": "JPN", "name_cn": "日本", "name_en": "Japan", "aliases": ["Japan", "日本国家队"], "group": "F"},
    {"fifa_code": "SWE", "name_cn": "瑞典", "name_en": "Sweden", "aliases": ["Sweden", "瑞典国家队"], "group": "F"},
    {"fifa_code": "TUN", "name_cn": "突尼斯", "name_en": "Tunisia", "aliases": ["Tunisia", "突尼斯国家队"], "group": "F"},
    {"fifa_code": "BEL", "name_cn": "比利时", "name_en": "Belgium", "aliases": ["Belgium", "比利时国家队"], "group": "G"},
    {"fifa_code": "EGY", "name_cn": "埃及", "name_en": "Egypt", "aliases": ["Egypt", "埃及国家队"], "group": "G"},
    {"fifa_code": "IRN", "name_cn": "伊朗", "name_en": "IR Iran", "aliases": ["IR Iran", "Iran", "伊朗国家队", "伊朗"], "group": "G"},
    {"fifa_code": "NZL", "name_cn": "新西兰", "name_en": "New Zealand", "aliases": ["New Zealand", "新西兰国家队"], "group": "G"},
    {"fifa_code": "ESP", "name_cn": "西班牙", "name_en": "Spain", "aliases": ["Spain", "西班牙国家队"], "group": "H"},
    {"fifa_code": "CPV", "name_cn": "佛得角", "name_en": "Cabo Verde", "aliases": ["Cabo Verde", "Cape Verde", "佛得角国家队"], "group": "H"},
    {"fifa_code": "KSA", "name_cn": "沙特阿拉伯", "name_en": "Saudi Arabia", "aliases": ["Saudi Arabia", "沙特", "沙特阿拉伯国家队"], "group": "H"},
    {"fifa_code": "URU", "name_cn": "乌拉圭", "name_en": "Uruguay", "aliases": ["Uruguay", "乌拉圭国家队"], "group": "H"},
    {"fifa_code": "FRA", "name_cn": "法国", "name_en": "France", "aliases": ["France", "法国国家队"], "group": "I"},
    {"fifa_code": "SEN", "name_cn": "塞内加尔", "name_en": "Senegal", "aliases": ["Senegal", "塞内加尔国家队"], "group": "I"},
    {"fifa_code": "IRQ", "name_cn": "伊拉克", "name_en": "Iraq", "aliases": ["Iraq", "伊拉克国家队"], "group": "I"},
    {"fifa_code": "NOR", "name_cn": "挪威", "name_en": "Norway", "aliases": ["Norway", "挪威国家队"], "group": "I"},
    {"fifa_code": "ARG", "name_cn": "阿根廷", "name_en": "Argentina", "aliases": ["Argentina", "阿根廷国家队"], "group": "J"},
    {"fifa_code": "ALG", "name_cn": "阿尔及利亚", "name_en": "Algeria", "aliases": ["Algeria", "阿尔及利亚国家队"], "group": "J"},
    {"fifa_code": "AUT", "name_cn": "奥地利", "name_en": "Austria", "aliases": ["Austria", "奥地利国家队"], "group": "J"},
    {"fifa_code": "JOR", "name_cn": "约旦", "name_en": "Jordan", "aliases": ["Jordan", "约旦国家队"], "group": "J"},
    {"fifa_code": "POR", "name_cn": "葡萄牙", "name_en": "Portugal", "aliases": ["Portugal", "葡萄牙国家队"], "group": "K"},
    {"fifa_code": "COD", "name_cn": "刚果（金）", "name_en": "DR Congo", "aliases": ["DR Congo", "Congo DR", "刚果（金）国家队"], "group": "K"},
    {"fifa_code": "UZB", "name_cn": "乌兹别克斯坦", "name_en": "Uzbekistan", "aliases": ["Uzbekistan", "乌兹别克斯坦国家队"], "group": "K"},
    {"fifa_code": "COL", "name_cn": "哥伦比亚", "name_en": "Colombia", "aliases": ["Colombia", "哥伦比亚国家队"], "group": "K"},
    {"fifa_code": "ENG", "name_cn": "英格兰", "name_en": "England", "aliases": ["England", "英格兰国家队"], "group": "L"},
    {"fifa_code": "CRO", "name_cn": "克罗地亚", "name_en": "Croatia", "aliases": ["Croatia", "克罗地亚国家队"], "group": "L"},
    {"fifa_code": "GHA", "name_cn": "加纳", "name_en": "Ghana", "aliases": ["Ghana", "加纳国家队"], "group": "L"},
    {"fifa_code": "PAN", "name_cn": "巴拿马", "name_en": "Panama", "aliases": ["Panama", "巴拿马国家队"], "group": "L"},
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_number(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        if "." in str(value):
            return round(float(value), 2)
        return int(value)
    except (TypeError, ValueError):
        return value


class TeamDataService:
    """管理世界杯预测所需的结构化球队数据。"""

    @classmethod
    def ensure_storage(cls) -> None:
        os.makedirs(TEAM_DATA_DIR, exist_ok=True)
        if not os.path.exists(TEAM_DATA_FILE):
            cls.save_database(cls._empty_database())

    @classmethod
    def _empty_database(cls) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "source": "FIFA inside world ranking pages",
            "updated_at": None,
            "team_registry": DEFAULT_TEAM_REGISTRY,
            "teams": [],
        }

    @classmethod
    def load_database(cls) -> dict[str, Any]:
        cls.ensure_storage()
        try:
            with open(TEAM_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = cls._empty_database()

        data.setdefault("schema_version", "1.0")
        data.setdefault("source", "FIFA inside world ranking pages")
        data.setdefault("updated_at", None)
        data["team_registry"] = data.get("team_registry") or DEFAULT_TEAM_REGISTRY
        data["teams"] = data.get("teams") or []
        return data

    @classmethod
    def save_database(cls, data: dict[str, Any]) -> None:
        cls.ensure_storage()
        data["updated_at"] = _utc_now()
        with open(TEAM_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def normalize_name(cls, name: str | None) -> str:
        return (name or "").strip().lower()

    @classmethod
    def _record_names(cls, team: dict[str, Any]) -> set[str]:
        names = {
            cls.normalize_name(team.get("name_cn")),
            cls.normalize_name(team.get("name_en")),
            cls.normalize_name(team.get("fifa_code")),
        }
        aliases = team.get("aliases") or []
        names.update(cls.normalize_name(alias) for alias in aliases)
        return {name for name in names if name}

    @classmethod
    def _registry_names(cls, item: dict[str, Any]) -> set[str]:
        names = {
            cls.normalize_name(item.get("name_cn")),
            cls.normalize_name(item.get("name_en")),
            cls.normalize_name(item.get("fifa_code")),
        }
        aliases = item.get("aliases") or []
        names.update(cls.normalize_name(alias) for alias in aliases)
        return {name for name in names if name}

    @classmethod
    def get_world_cup_2026_registry(cls) -> list[dict[str, Any]]:
        return WORLD_CUP_2026_REGISTRY

    @classmethod
    def merge_registry_entries(cls, entries: list[dict[str, Any]]) -> None:
        db = cls.load_database()
        registry = db.get("team_registry", [])
        by_code = {
            cls.normalize_name(item.get("fifa_code")): item
            for item in registry
            if item.get("fifa_code")
        }
        for entry in entries:
            code = cls.normalize_name(entry.get("fifa_code"))
            if not code:
                continue
            existing = by_code.get(code, {})
            merged_aliases = sorted(set((existing.get("aliases") or []) + (entry.get("aliases") or [])))
            merged = {
                **existing,
                **entry,
                "aliases": merged_aliases,
            }
            by_code[code] = merged
        db["team_registry"] = sorted(
            by_code.values(),
            key=lambda item: (item.get("group") or "Z", item.get("name_cn") or item.get("name_en") or item.get("fifa_code") or ""),
        )
        cls.save_database(db)

    @classmethod
    def resolve_registry_entry(cls, team_name: str | None = None, fifa_code: str | None = None) -> dict[str, Any] | None:
        db = cls.load_database()
        target_name = cls.normalize_name(team_name)
        target_code = cls.normalize_name(fifa_code)
        for item in db.get("team_registry", []):
            if target_code and cls.normalize_name(item.get("fifa_code")) == target_code:
                return item
            if target_name and target_name in cls._registry_names(item):
                return item
        return None

    @classmethod
    def get_all_teams(cls) -> list[str]:
        db = cls.load_database()
        names = []
        for team in db.get("teams", []):
            display_name = team.get("name_cn") or team.get("name_en") or team.get("fifa_code")
            if display_name:
                names.append(display_name)
        return sorted(set(names))

    @classmethod
    def get_world_cup_2026_teams(cls) -> list[str]:
        db = cls.load_database()
        names = []
        for team in db.get("teams", []):
            tournament = team.get("world_cup_2026") or {}
            if not tournament.get("qualified"):
                continue
            display_name = team.get("name_cn") or team.get("name_en") or team.get("fifa_code")
            if display_name:
                names.append(display_name)
        return sorted(set(names))

    @classmethod
    def get_team(cls, team_name: str) -> dict[str, Any] | None:
        db = cls.load_database()
        target = cls.normalize_name(team_name)
        for team in db.get("teams", []):
            if target in cls._record_names(team):
                return team
        return None

    @classmethod
    def get_team_identity_tokens(cls, team_name: str) -> list[str]:
        team = cls.get_team(team_name)
        tokens = []
        if not team:
            return [team_name] if team_name else []

        for key in ["name_cn", "name_en", "fifa_code"]:
            value = team.get(key)
            if value:
                tokens.append(str(value).strip())

        for alias in team.get("aliases") or []:
            if alias:
                tokens.append(str(alias).strip())

        name_cn = team.get("name_cn")
        name_en = team.get("name_en")
        if name_cn:
            tokens.append(f"{name_cn}队")
            tokens.append(f"{name_cn}国家队")
        if name_en:
            tokens.append(f"{name_en} national team")

        deduped = []
        seen = set()
        for token in tokens:
            normalized = cls.normalize_name(token)
            if token and normalized not in seen:
                deduped.append(token)
                seen.add(normalized)
        return deduped

    @classmethod
    def upsert_team(cls, team_record: dict[str, Any]) -> dict[str, Any]:
        db = cls.load_database()
        teams = db.get("teams", [])
        target_code = cls.normalize_name(team_record.get("fifa_code"))
        target_names = cls._record_names(team_record)

        replaced = False
        for index, existing in enumerate(teams):
            existing_code = cls.normalize_name(existing.get("fifa_code"))
            if (target_code and existing_code == target_code) or target_names.intersection(cls._record_names(existing)):
                teams[index] = team_record
                replaced = True
                break

        if not replaced:
            teams.append(team_record)

        db["teams"] = sorted(
            teams,
            key=lambda item: (
                item.get("ranking", {}).get("current_rank") is None,
                item.get("ranking", {}).get("current_rank") or 9999,
                item.get("name_cn") or item.get("name_en") or item.get("fifa_code") or "",
            ),
        )
        cls.save_database(db)
        return team_record

    @classmethod
    def ensure_uploaded_team_entry(cls, team_name: str) -> None:
        if cls.get_team(team_name):
            return

        registry = cls.resolve_registry_entry(team_name=team_name)
        fallback = {
            "name_cn": team_name,
            "name_en": registry.get("name_en") if registry else "",
            "aliases": sorted(set([team_name] + (registry.get("aliases", []) if registry else []))),
            "fifa_code": registry.get("fifa_code") if registry else None,
            "profile_url": None,
            "last_synced_at": None,
            "source": "local_upload",
            "ranking": {
                "current_rank": None,
                "current_points": None,
                "previous_rank": None,
                "previous_points": None,
                "points_difference": None,
                "last_update_date": None,
                "next_update_date": None,
                "history_highlights": {},
            },
            "historical_rankings": [],
            "recent_matches": [],
            "upcoming_matches": [],
        }
        if registry and registry.get("group"):
            fallback["world_cup_2026"] = {
                "qualified": True,
                "group": registry["group"],
            }
        cls.upsert_team(fallback)

    @classmethod
    def build_team_analysis_text(cls, team_name: str) -> str:
        team = cls.get_team(team_name)
        if not team:
            return ""

        ranking = team.get("ranking", {})
        history = ranking.get("history_highlights", {})
        lines = []
        display_name = team.get("name_cn") or team.get("name_en") or team_name
        lines.append(f"【FIFA结构化数据】{display_name}")

        fifa_code = team.get("fifa_code")
        if fifa_code:
            lines.append(f"- FIFA代码：{fifa_code}")

        tournament = team.get("world_cup_2026") or {}
        if tournament.get("qualified"):
            group = tournament.get("group")
            lines.append(f"- 世界杯2026：已入围{f'，分组 {group} 组' if group else ''}")

        current_rank = ranking.get("current_rank")
        current_points = ranking.get("current_points")
        previous_rank = ranking.get("previous_rank")
        points_diff = ranking.get("points_difference")
        if current_rank is not None:
            rank_text = f"当前世界排名第 {current_rank} 位"
            if current_points is not None:
                rank_text += f"，积分 {current_points}"
            if previous_rank is not None:
                rank_text += f"，上期排名第 {previous_rank} 位"
            if points_diff not in (None, ""):
                rank_text += f"，积分变化 {points_diff:+}"
            lines.append(f"- {rank_text}")

        history_fragments = []
        mapping = {
            "Current rank": "当前排名",
            "Highest Ranking": "历史最高排名",
            "Lowest Rank": "历史最低排名",
            "Average Rank": "平均排名",
            "Biggest climb": "最大升幅",
            "Biggest fall": "最大跌幅",
        }
        for key, label in mapping.items():
            value = history.get(key)
            if value not in (None, ""):
                history_fragments.append(f"{label} {value}")
        if history_fragments:
            lines.append(f"- 排名历史：{'；'.join(history_fragments)}")

        recent_matches = team.get("recent_matches") or []
        if recent_matches:
            lines.append("- 近期比赛：")
            for match in recent_matches[:5]:
                competition = match.get("competition") or "国际比赛"
                opponent = match.get("opponent_name") or match.get("opponent_code") or "未知对手"
                score = match.get("score") or "待定"
                outcome = match.get("outcome") or "待定"
                lines.append(f"  - {match.get('date', '未知日期')} {competition} 对阵 {opponent}，比分 {score}，结果 {outcome}")

        upcoming_matches = team.get("upcoming_matches") or []
        if upcoming_matches:
            lines.append("- 未来赛程：")
            for match in upcoming_matches[:3]:
                competition = match.get("competition") or "国际比赛"
                opponent = match.get("opponent_name") or match.get("opponent_code") or "未知对手"
                kickoff = match.get("kickoff") or match.get("date") or "待定"
                lines.append(f"  - {kickoff} {competition} 对阵 {opponent}")

        recent_history = team.get("historical_rankings") or []
        if recent_history:
            formatted = []
            for item in recent_history[:5]:
                year = item.get("year")
                final_rank = item.get("final_rank")
                best_rank = item.get("best_rank")
                worst_rank = item.get("worst_rank")
                if year and final_rank is not None:
                    formatted.append(f"{year}年最终第{final_rank}位（最好{best_rank}，最差{worst_rank}）")
            if formatted:
                lines.append(f"- 近年走势：{'；'.join(formatted)}")

        squad_profile = WORLD_CUP_2026_SQUAD_PROFILES.get(team.get("fifa_code") or "")
        tournament = team.get("world_cup_2026") or {}
        summary_cn = tournament.get("squad_profile_summary") or (squad_profile.get("summary_cn") if squad_profile else None)
        if summary_cn:
            lines.append(f"- 世界杯阵容摘要：{summary_cn}")

        key_players = tournament.get("key_players") or WorldCupPlayerProfileService.get_key_players(
            fifa_code=team.get("fifa_code") or "",
            team_name=display_name,
        )
        if key_players:
            lines.append("- 世界杯关键球员：")
            for player in key_players[:8]:
                role = player.get("role") or "球员"
                traits = "、".join(player.get("style_traits") or [])
                summary = player.get("style_summary") or ""
                extra = f"；特点：{traits}" if traits else ""
                if summary:
                    extra += f"；说明：{summary}"
                lines.append(f"  - {player.get('name')}（{role}）{extra}")

        return "\n".join(lines)

    @classmethod
    def enrich_world_cup_player_profiles(cls) -> dict[str, int]:
        db = cls.load_database()
        teams = db.get("teams", [])
        updated = 0
        covered = 0

        for team in teams:
            fifa_code = team.get("fifa_code") or ""
            tournament = team.get("world_cup_2026") or {}
            if not tournament.get("qualified"):
                continue

            display_name = team.get("name_cn") or team.get("name_en") or fifa_code
            squad_profile = WORLD_CUP_2026_SQUAD_PROFILES.get(fifa_code) or {}
            key_players = WorldCupPlayerProfileService.get_key_players(fifa_code=fifa_code, team_name=display_name)

            if squad_profile.get("summary_cn") or key_players:
                tournament["squad_source"] = "FIFA official squad announcement summaries"
                tournament["squad_data_status"] = "partial"
                if squad_profile.get("summary_cn"):
                    tournament["squad_profile_summary"] = squad_profile["summary_cn"]
                if key_players:
                    tournament["key_players"] = key_players
                team["world_cup_2026"] = tournament
                updated += 1
                if key_players:
                    covered += 1

        db["teams"] = teams
        cls.save_database(db)
        return {"updated_teams": updated, "teams_with_players": covered}

    @classmethod
    def build_graph_seed_text(cls, team_name: str) -> str:
        team = cls.get_team(team_name)
        if not team:
            return ""

        display_name = team.get("name_cn") or team.get("name_en") or team_name
        name_en = team.get("name_en") or ""
        fifa_code = team.get("fifa_code") or ""
        aliases = "、".join(team.get("aliases") or [])
        summary = cls.build_team_analysis_text(team_name)

        lines = [
            f"主题球队：{display_name}国家队",
            f"唯一主体：以下全部内容只描述{display_name}国家队，不描述其他国家队。",
        ]
        if name_en:
            lines.append(f"英文名：{name_en}")
        if fifa_code:
            lines.append(f"FIFA代码：{fifa_code}")
        if aliases:
            lines.append(f"别名：{aliases}")
        lines.append("球队档案：")
        for line in summary.splitlines():
            if line.strip():
                lines.append(f"{display_name}国家队{line if line.startswith('：') else '：' + line}")

        return "\n".join(lines)

    @classmethod
    def simplify_highlights(cls, items: list[dict[str, Any]] | None) -> dict[str, Any]:
        result = {}
        for item in items or []:
            label = item.get("label")
            value = item.get("value")
            if label:
                result[label] = value
        return result

    @classmethod
    def normalize_history_rows(cls, rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        normalized = []
        for row in rows or []:
            normalized.append(
                {
                    "year": row.get("year"),
                    "final_rank": _safe_number(row.get("finalRank")),
                    "best_rank": _safe_number(row.get("bestRank")),
                    "worst_rank": _safe_number(row.get("worstRank")),
                    "biggest_climb": _safe_number(row.get("biggestClimb")),
                    "biggest_fall": _safe_number(row.get("biggestFall")),
                    "biggest_climb_month": row.get("biggestClimbMonth"),
                    "biggest_fall_month": row.get("biggestFallMonth"),
                }
            )
        return normalized

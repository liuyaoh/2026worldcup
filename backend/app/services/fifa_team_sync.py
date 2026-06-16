import json
import re
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from typing import Any

from .team_data_service import TeamDataService


class FifaTeamSyncService:
    BASE_URL_TEMPLATE = "https://inside.fifa.com/fifa-world-ranking/{code}?gender=men"
    REQUEST_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
    }

    @classmethod
    def sync_teams(
        cls,
        team_names: list[str] | None = None,
        team_codes: list[str] | None = None,
        scope: str | None = None,
    ) -> dict[str, Any]:
        targets = cls._resolve_targets(team_names=team_names, team_codes=team_codes, scope=scope)
        TeamDataService.merge_registry_entries(targets)
        synced = []
        failed = []

        for item in targets:
            try:
                record = cls.fetch_team_record(item)
                TeamDataService.upsert_team(record)
                synced.append(
                    {
                        "name": record.get("name_cn") or record.get("name_en") or record.get("fifa_code"),
                        "fifa_code": record.get("fifa_code"),
                        "current_rank": record.get("ranking", {}).get("current_rank"),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                failed.append(
                    {
                        "name": item.get("name_cn") or item.get("name_en") or item.get("fifa_code"),
                        "fifa_code": item.get("fifa_code"),
                        "error": str(exc),
                    }
                )

        return {
            "requested_count": len(targets),
            "synced_count": len(synced),
            "failed_count": len(failed),
            "synced": synced,
            "failed": failed,
        }

    @classmethod
    def fetch_team_record(cls, target: dict[str, Any]) -> dict[str, Any]:
        fifa_code = target["fifa_code"]
        url = cls.BASE_URL_TEMPLATE.format(code=fifa_code)
        next_data = cls._fetch_next_data(url)
        page_data = next_data["props"]["pageProps"]["pageData"]
        ranking_data = page_data["ranking"]["rankings"]["menRanking"]
        row = next(
            (item for item in (ranking_data.get("rows") or []) if item.get("countryCode") == fifa_code),
            None,
        )
        if not row:
            raise ValueError(f"未能从 FIFA 页面提取到 {fifa_code} 的排名数据")

        history_section = (page_data.get("historyRanking") or {}).get("1", {})
        history_highlights = TeamDataService.simplify_highlights(
            history_section.get("statistic", {}).get("highlightsItems")
        )
        history_rows = TeamDataService.normalize_history_rows(
            history_section.get("historyTable", {}).get("rows")
        )

        recent_matches, upcoming_matches = cls._extract_matches(
            row.get("matchesWindow"),
            focus_code=row.get("countryCode") or fifa_code,
        )

        aliases = []
        aliases.extend(target.get("aliases") or [])
        aliases.extend(filter(None, [row.get("name"), target.get("name_cn"), target.get("name_en"), fifa_code]))
        aliases = sorted({alias.strip() for alias in aliases if alias and alias.strip()})

        record = {
            "name_cn": target.get("name_cn") or row.get("name"),
            "name_en": row.get("name") or target.get("name_en"),
            "aliases": aliases,
            "fifa_code": row.get("countryCode") or fifa_code,
            "profile_url": cls._absolute_url(row.get("countryURL") or url),
            "source": "fifa",
            "last_synced_at": datetime.now(timezone.utc).isoformat(),
            "ranking": {
                "current_rank": row.get("rank"),
                "current_points": cls._round_number(row.get("totalPoints")),
                "previous_rank": row.get("previousRank"),
                "previous_points": cls._round_number(row.get("previousPoints")),
                "points_difference": cls._round_number(row.get("pointsDifference")),
                "last_update_date": ranking_data.get("lastUpdateDate") or row.get("lastUpdateDate"),
                "next_update_date": ranking_data.get("nextUpdateDate") or row.get("nextUpdateDate"),
                "history_highlights": history_highlights,
            },
            "historical_rankings": history_rows[:8],
            "recent_matches": recent_matches[:8],
            "upcoming_matches": upcoming_matches[:5],
        }
        if target.get("group"):
            record["world_cup_2026"] = {
                "qualified": True,
                "group": target["group"],
            }
        return record

    @classmethod
    def _resolve_targets(
        cls,
        team_names: list[str] | None = None,
        team_codes: list[str] | None = None,
        scope: str | None = None,
    ) -> list[dict[str, Any]]:
        if scope == "world_cup_2026":
            return TeamDataService.get_world_cup_2026_registry()

        db = TeamDataService.load_database()
        registry = db.get("team_registry", [])

        if not team_names and not team_codes:
            return registry

        resolved = []
        seen_codes = set()

        for code in team_codes or []:
            item = TeamDataService.resolve_registry_entry(fifa_code=code)
            if item and item["fifa_code"] not in seen_codes:
                resolved.append(item)
                seen_codes.add(item["fifa_code"])

        for name in team_names or []:
            item = TeamDataService.resolve_registry_entry(team_name=name)
            if item and item["fifa_code"] not in seen_codes:
                resolved.append(item)
                seen_codes.add(item["fifa_code"])

        if not resolved:
            raise ValueError("没有匹配到可同步的 FIFA 球队，请确认球队名称或代码已在注册表中")

        return resolved

    @classmethod
    def _fetch_next_data(cls, url: str) -> dict[str, Any]:
        request = urllib.request.Request(url, headers=cls.REQUEST_HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                html = response.read().decode("utf-8", "ignore")
        except urllib.error.URLError as exc:
            raise ValueError(f"访问 FIFA 页面失败: {exc}") from exc

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html,
            re.S,
        )
        if not match:
            raise ValueError("FIFA 页面中未找到 __NEXT_DATA__ 数据")
        return json.loads(match.group(1))

    @classmethod
    def _extract_matches(cls, payload: Any, focus_code: str | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        collected: dict[str, dict[str, Any]] = {}
        cls._collect_match_dicts(payload, collected)
        parsed = []
        for raw_match in collected.values():
            normalized = cls._normalize_match(raw_match, focus_code=focus_code)
            if normalized:
                parsed.append(normalized)

        today = date.today().isoformat()
        recent_matches = sorted(
            [item for item in parsed if item.get("date") and item["date"] < today],
            key=lambda item: item["date"],
            reverse=True,
        )
        upcoming_matches = sorted(
            [item for item in parsed if item.get("date") and item["date"] >= today],
            key=lambda item: (item["date"], item.get("kickoff") or ""),
        )
        return recent_matches, upcoming_matches

    @classmethod
    def _collect_match_dicts(cls, node: Any, collected: dict[str, dict[str, Any]]) -> None:
        if isinstance(node, dict):
            if {"IdMatch", "Date", "Home", "Away"}.issubset(node.keys()):
                collected[str(node["IdMatch"])] = node
            for value in node.values():
                cls._collect_match_dicts(value, collected)
        elif isinstance(node, list):
            for item in node:
                cls._collect_match_dicts(item, collected)

    @classmethod
    def _normalize_match(cls, match: dict[str, Any], focus_code: str | None) -> dict[str, Any] | None:
        home = match.get("Home") or {}
        away = match.get("Away") or {}
        home_code = home.get("IdCountry")
        away_code = away.get("IdCountry")
        if focus_code and focus_code not in {home_code, away_code}:
            return None

        is_home = focus_code == home_code if focus_code else True
        team_side = home if is_home else away
        opponent_side = away if is_home else home

        team_score = match.get("HomeTeamScore") if is_home else match.get("AwayTeamScore")
        opponent_score = match.get("AwayTeamScore") if is_home else match.get("HomeTeamScore")

        outcome = "待定"
        if isinstance(team_score, int) and isinstance(opponent_score, int):
            if team_score > opponent_score:
                outcome = "胜"
            elif team_score < opponent_score:
                outcome = "负"
            else:
                outcome = "平"

        score = None
        if team_score is not None and opponent_score is not None:
            score = f"{team_score}:{opponent_score}"

        competition = (
            cls._locale_text(match.get("SeasonName"))
            or cls._locale_text(match.get("CompetitionName"))
            or cls._locale_text(match.get("GroupName"))
            or cls._locale_text(match.get("StageName"))
        )

        return {
            "match_id": match.get("IdMatch"),
            "date": match.get("Date"),
            "kickoff": match.get("MatchTime") or match.get("LocalDate") or match.get("Date"),
            "competition": competition,
            "is_home": is_home,
            "opponent_name": cls._locale_text(opponent_side.get("TeamName")),
            "opponent_code": opponent_side.get("IdCountry"),
            "team_name": cls._locale_text(team_side.get("TeamName")),
            "team_code": team_side.get("IdCountry"),
            "score": score,
            "outcome": outcome,
        }

    @classmethod
    def _locale_text(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and item.get("Description"):
                    return item["Description"]
        if isinstance(value, dict):
            return value.get("Description") or value.get("description")
        return str(value)

    @classmethod
    def _absolute_url(cls, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("/"):
            return f"https://inside.fifa.com{url}"
        return url

    @classmethod
    def _round_number(cls, value: Any) -> Any:
        if value in (None, ""):
            return None
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return value

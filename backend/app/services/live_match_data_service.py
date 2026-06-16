import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from ..config import Config
from ..utils.logger import get_logger
from .team_data_service import TeamDataService


logger = get_logger("world_cup.live_data")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _truncate(text: str | None, limit: int = 80) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _resolve_team_name(name: str | None) -> str:
    entry = TeamDataService.resolve_registry_entry(team_name=name)
    if entry:
        return entry.get("name_cn") or entry.get("name_en") or name or ""
    return (name or "").strip()


def _team_name_candidates(name: str | None) -> set[str]:
    entry = TeamDataService.resolve_registry_entry(team_name=name)
    candidates = set()
    if entry:
        for key in ("name_cn", "name_en", "fifa_code"):
            value = entry.get(key)
            if value:
                candidates.add(TeamDataService.normalize_name(str(value)))
        for alias in entry.get("aliases") or []:
            if alias:
                candidates.add(TeamDataService.normalize_name(str(alias)))
    if name:
        candidates.add(TeamDataService.normalize_name(name))
    return {candidate for candidate in candidates if candidate}


def _match_side(team_name: str | None, _home_name: str, away_name: str) -> str:
    normalized = (team_name or "").strip().lower()
    if normalized and normalized == away_name.strip().lower():
        return "team_b"
    return "team_a"


class FootballDataLiveProvider:
    provider_id = "football-data"
    provider_label = "football-data.org"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(Config.FOOTBALL_DATA_API_KEY)

    @classmethod
    def _request_json(cls, path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
        if not cls.is_configured():
            raise ValueError("未配置 FOOTBALL_DATA_API_KEY，无法连接真实直播数据源")

        base_url = (Config.FOOTBALL_DATA_BASE_URL or "https://api.football-data.org").rstrip("/")
        query = {key: value for key, value in (query or {}).items() if value not in (None, "")}
        query_string = urllib.parse.urlencode(query)
        url = f"{base_url}{path}"
        if query_string:
            url = f"{url}?{query_string}"

        request = urllib.request.Request(
            url,
            headers={
                "X-Auth-Token": Config.FOOTBALL_DATA_API_KEY,
                "Accept": "application/json",
                "User-Agent": "WorldCupWinProbability/1.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8", "ignore"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "ignore")
            raise ValueError(f"football-data 请求失败：HTTP {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise ValueError(f"football-data 请求失败：{exc}") from exc

    @classmethod
    def list_matches(cls, date: str | None = None, live_only: bool = False) -> list[dict[str, Any]]:
        competition_code = Config.FOOTBALL_DATA_WORLD_CUP_CODE or "WC"
        query: dict[str, Any] = {}
        if live_only:
            query["status"] = "LIVE"
        elif date:
            query["dateFrom"] = date
            query["dateTo"] = date

        data = cls._request_json(f"/v4/competitions/{competition_code}/matches", query=query)
        matches = data.get("matches") or []
        return [cls._normalize_match_summary(match) for match in matches]

    @classmethod
    def get_match(cls, fixture_id: str | int) -> dict[str, Any]:
        data = cls._request_json(f"/v4/matches/{fixture_id}")
        match = data.get("match") or data
        return cls._normalize_match_detail(match)

    @classmethod
    def _normalize_match_summary(cls, match: dict[str, Any]) -> dict[str, Any]:
        home_team = ((match.get("homeTeam") or {}).get("name") or "").strip()
        away_team = ((match.get("awayTeam") or {}).get("name") or "").strip()
        score = match.get("score") or {}
        full_time = score.get("fullTime") or {}
        minute = _safe_int(match.get("minute"), 0)
        return {
            "fixture_id": str(match.get("id") or ""),
            "provider": cls.provider_id,
            "status": match.get("status") or "",
            "minute": minute,
            "kickoff": match.get("utcDate") or "",
            "competition_name": ((match.get("competition") or {}).get("name") or "").strip(),
            "stage": match.get("stage") or "",
            "group": match.get("group") or "",
            "home_team": home_team,
            "away_team": away_team,
            "home_team_cn": _resolve_team_name(home_team),
            "away_team_cn": _resolve_team_name(away_team),
            "score_a": _safe_int(full_time.get("home"), _safe_int(full_time.get("homeTeam"), 0)),
            "score_b": _safe_int(full_time.get("away"), _safe_int(full_time.get("awayTeam"), 0)),
            "label": f"{_resolve_team_name(home_team)} vs {_resolve_team_name(away_team)}",
        }

    @classmethod
    def _normalize_match_detail(cls, match: dict[str, Any]) -> dict[str, Any]:
        home_team = ((match.get("homeTeam") or {}).get("name") or "").strip()
        away_team = ((match.get("awayTeam") or {}).get("name") or "").strip()
        home_team_cn = _resolve_team_name(home_team)
        away_team_cn = _resolve_team_name(away_team)
        score = match.get("score") or {}
        full_time = score.get("fullTime") or {}
        minute = _safe_int(match.get("minute"), 0)
        goals = match.get("goals") or []
        bookings = match.get("bookings") or []
        substitutions = match.get("substitutions") or []
        events: list[dict[str, Any]] = []
        red_cards_a = 0
        red_cards_b = 0
        yellow_cards_a = 0
        yellow_cards_b = 0

        for goal in goals:
            team_name = ((goal.get("team") or {}).get("name") or "").strip()
            side = _match_side(team_name, home_team, away_team)
            scorer = ((goal.get("scorer") or {}).get("name") or "").strip()
            extra = f"（{scorer}）" if scorer else ""
            events.append({
                "minute": _safe_int(goal.get("minute"), minute),
                "team": side,
                "type": "goal",
                "description": f"进球{extra}",
            })

        for booking in bookings:
            team_name = ((booking.get("team") or {}).get("name") or "").strip()
            side = _match_side(team_name, home_team, away_team)
            card = (booking.get("card") or "").upper()
            player_name = ((booking.get("player") or {}).get("name") or "").strip()
            description = player_name or "吃牌"
            if "RED" in card:
                if side == "team_a":
                    red_cards_a += 1
                else:
                    red_cards_b += 1
                events.append({
                    "minute": _safe_int(booking.get("minute"), minute),
                    "team": side,
                    "type": "red_card",
                    "description": f"{description} 吃到红牌",
                })
            else:
                if side == "team_a":
                    yellow_cards_a += 1
                else:
                    yellow_cards_b += 1
                events.append({
                    "minute": _safe_int(booking.get("minute"), minute),
                    "team": side,
                    "type": "yellow_card",
                    "description": f"{description} 吃到黄牌",
                })

        for substitution in substitutions:
            team_name = ((substitution.get("team") or {}).get("name") or "").strip()
            side = _match_side(team_name, home_team, away_team)
            player_out = ((substitution.get("playerOut") or {}).get("name") or "").strip()
            player_in = ((substitution.get("playerIn") or {}).get("name") or "").strip()
            details = "换人调整"
            if player_out or player_in:
                details = f"{player_out or '球员'} -> {player_in or '球员'}"
            events.append({
                "minute": _safe_int(substitution.get("minute"), minute),
                "team": side,
                "type": "substitution",
                "description": details,
            })

        events.sort(key=lambda item: item.get("minute", 0), reverse=True)
        score_a = _safe_int(full_time.get("home"), _safe_int(full_time.get("homeTeam"), 0))
        score_b = _safe_int(full_time.get("away"), _safe_int(full_time.get("awayTeam"), 0))
        live_state = {
            "minute": minute,
            "scoreA": score_a,
            "scoreB": score_b,
            "redCardsA": red_cards_a,
            "redCardsB": red_cards_b,
            "yellowCardsA": yellow_cards_a,
            "yellowCardsB": yellow_cards_b,
            "possessionA": 50,
            "possessionB": 50,
            "shotsOnTargetA": 0,
            "shotsOnTargetB": 0,
            "xgA": 0,
            "xgB": 0,
            "dangerousAttacksA": 0,
            "dangerousAttacksB": 0,
            "injuriesA": 0,
            "injuriesB": 0,
            "momentum": "balanced",
            "notes": "",
            "events": events,
        }
        return {
            "provider": cls.provider_id,
            "fixture_id": str(match.get("id") or ""),
            "competition_name": ((match.get("competition") or {}).get("name") or "").strip(),
            "status": match.get("status") or "",
            "minute": minute,
            "kickoff": match.get("utcDate") or "",
            "stage": match.get("stage") or "",
            "group": match.get("group") or "",
            "venue": match.get("venue") or "",
            "home_team": home_team,
            "away_team": away_team,
            "home_team_cn": home_team_cn,
            "away_team_cn": away_team_cn,
            "live_state": live_state,
            "recent_events": [f"第 {event['minute']} 分钟，{_truncate(event['description'])}" for event in events[:5]],
            "raw_score": {
                "score_a": score_a,
                "score_b": score_b,
            },
        }


class LiveMatchDataService:
    PROVIDERS = {
        FootballDataLiveProvider.provider_id: FootballDataLiveProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str | None = None):
        provider_key = (provider_name or Config.LIVE_DATA_PROVIDER or FootballDataLiveProvider.provider_id).strip().lower()
        provider = cls.PROVIDERS.get(provider_key)
        if not provider:
            raise ValueError(f"不支持的数据源：{provider_key}")
        return provider

    @classmethod
    def get_provider_options(cls) -> list[dict[str, Any]]:
        default_provider = (Config.LIVE_DATA_PROVIDER or FootballDataLiveProvider.provider_id).strip().lower()
        options = []
        for provider_id, provider in cls.PROVIDERS.items():
            notice = ""
            recommended_poll = max(Config.LIVE_DATA_POLL_INTERVAL_SECONDS, 30)
            if provider_id == FootballDataLiveProvider.provider_id:
                notice = "免费版可用世界杯数据，但比分有延时，且通常不含首发、红牌等深度球员数据。"
            options.append({
                "id": provider_id,
                "label": provider.provider_label,
                "configured": provider.is_configured(),
                "is_default": provider_id == default_provider,
                "recommended_poll_seconds": recommended_poll,
                "notice": notice,
            })
        return options

    @classmethod
    def get_live_matches(cls, provider_name: str | None = None, date: str | None = None, live_only: bool = False) -> list[dict[str, Any]]:
        provider = cls.get_provider(provider_name)
        return provider.list_matches(date=date or _utc_today(), live_only=live_only)

    @classmethod
    def get_live_match_detail(cls, fixture_id: str | int, provider_name: str | None = None) -> dict[str, Any]:
        provider = cls.get_provider(provider_name)
        return provider.get_match(fixture_id)

    @classmethod
    def find_best_live_match(
        cls,
        provider_name: str | None = None,
        team_a: str | None = None,
        team_b: str | None = None,
        date: str | None = None,
        live_only: bool = True,
    ) -> dict[str, Any] | None:
        matches = cls.get_live_matches(provider_name=provider_name, date=date, live_only=live_only)
        if not matches:
            return None

        team_a_candidates = _team_name_candidates(team_a)
        team_b_candidates = _team_name_candidates(team_b)

        def match_names(match: dict[str, Any]) -> set[str]:
            names = {
                TeamDataService.normalize_name(match.get("home_team")),
                TeamDataService.normalize_name(match.get("away_team")),
                TeamDataService.normalize_name(match.get("home_team_cn")),
                TeamDataService.normalize_name(match.get("away_team_cn")),
            }
            return {name for name in names if name}

        def score_match(match: dict[str, Any]) -> tuple[int, int]:
            names = match_names(match)
            score = 0
            if team_a_candidates and team_a_candidates.intersection(names):
                score += 1
            if team_b_candidates and team_b_candidates.intersection(names):
                score += 1
            minute = _safe_int(match.get("minute"), 0)
            return score, minute

        ranked = sorted(matches, key=score_match, reverse=True)
        best = ranked[0]
        best_score, _ = score_match(best)

        if team_a_candidates or team_b_candidates:
            if best_score <= 0 and live_only:
                # 没有匹配到用户选择的球队时，回退到当前最接近正在直播中的世界杯比赛
                return best
        return best

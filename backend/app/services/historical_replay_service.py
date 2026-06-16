from typing import Any


def _replay_state_template() -> dict[str, Any]:
    return {
        "minute": 0,
        "scoreA": 0,
        "scoreB": 0,
        "redCardsA": 0,
        "redCardsB": 0,
        "yellowCardsA": 0,
        "yellowCardsB": 0,
        "possessionA": 50,
        "possessionB": 50,
        "shotsOnTargetA": 0,
        "shotsOnTargetB": 0,
        "xgA": 0.0,
        "xgB": 0.0,
        "dangerousAttacksA": 0,
        "dangerousAttacksB": 0,
        "injuriesA": 0,
        "injuriesB": 0,
        "momentum": "balanced",
        "notes": "",
        "events": [],
    }


HISTORICAL_REPLAYS = [
    {
        "id": "wc2022_final_arg_fra",
        "title": "2022 世界杯决赛",
        "subtitle": "阿根廷 vs 法国",
        "competition_name": "FIFA World Cup 2022",
        "stage": "FINAL",
        "team_a": "阿根廷",
        "team_b": "法国",
        "final_score": "阿根廷 3:3 法国（点球大战阿根廷胜）",
        "events": [
            {
                "minute": 21,
                "team": "team_a",
                "type": "momentum",
                "description": "阿根廷前场连续施压，比赛节奏明显偏向南美一侧。",
                "effects": {"dangerous_attacks_a": 3, "xg_a": 0.2, "shots_a": 1, "momentum": "team_a"},
            },
            {
                "minute": 23,
                "team": "team_a",
                "type": "goal",
                "description": "梅西点球命中，阿根廷 1:0 领先。",
                "effects": {"xg_a": 0.8, "shots_a": 1, "dangerous_attacks_a": 1, "momentum": "team_a"},
            },
            {
                "minute": 36,
                "team": "team_a",
                "type": "goal",
                "description": "迪马利亚反击破门，阿根廷把比分扩大为 2:0。",
                "effects": {"xg_a": 0.7, "shots_a": 1, "dangerous_attacks_a": 2, "momentum": "team_a"},
            },
            {
                "minute": 41,
                "team": "team_b",
                "type": "yellow_card",
                "description": "法国防线情绪上升，防守动作偏大吃到黄牌。",
                "effects": {"dangerous_attacks_b": 1},
            },
            {
                "minute": 68,
                "team": "team_b",
                "type": "momentum",
                "description": "法国换人后开始提速，比赛势头逐渐转向欧洲冠军。",
                "effects": {"dangerous_attacks_b": 3, "xg_b": 0.2, "shots_b": 1, "momentum": "team_b"},
            },
            {
                "minute": 80,
                "team": "team_b",
                "type": "goal",
                "description": "姆巴佩点球命中，法国追回一球。",
                "effects": {"xg_b": 0.75, "shots_b": 1, "dangerous_attacks_b": 1, "momentum": "team_b"},
            },
            {
                "minute": 81,
                "team": "team_b",
                "type": "goal",
                "description": "姆巴佩凌空抽射再下一城，法国迅速扳平为 2:2。",
                "effects": {"xg_b": 0.6, "shots_b": 1, "dangerous_attacks_b": 2, "momentum": "team_b"},
            },
            {
                "minute": 95,
                "team": "team_a",
                "type": "momentum",
                "description": "进入加时后阿根廷重新控制球权，连续制造威胁。",
                "effects": {"dangerous_attacks_a": 3, "xg_a": 0.25, "shots_a": 1, "momentum": "team_a"},
            },
            {
                "minute": 108,
                "team": "team_a",
                "type": "goal",
                "description": "梅西补射破门，阿根廷在加时赛再次领先。",
                "effects": {"xg_a": 0.7, "shots_a": 1, "dangerous_attacks_a": 2, "momentum": "team_a"},
            },
            {
                "minute": 115,
                "team": "team_b",
                "type": "xg_chance",
                "description": "法国持续冲击禁区，制造极高质量机会。",
                "effects": {"xg_b": 0.45, "shots_b": 1, "dangerous_attacks_b": 2, "momentum": "team_b"},
            },
            {
                "minute": 118,
                "team": "team_b",
                "type": "goal",
                "description": "姆巴佩再次点球命中，法国把比分追成 3:3。",
                "effects": {"xg_b": 0.78, "shots_b": 1, "dangerous_attacks_b": 1, "momentum": "team_b"},
            },
            {
                "minute": 123,
                "team": "team_a",
                "type": "shot_on_target",
                "description": "阿根廷最后时刻形成门前绝杀机会，但被扑出。",
                "effects": {"xg_a": 0.35, "shots_a": 1, "dangerous_attacks_a": 2, "momentum": "team_a"},
            },
        ],
    }
]


class HistoricalReplayService:
    @classmethod
    def list_replays(cls) -> list[dict[str, Any]]:
        return [
            {
                "id": replay["id"],
                "title": replay["title"],
                "subtitle": replay["subtitle"],
                "competition_name": replay["competition_name"],
                "stage": replay["stage"],
                "team_a": replay["team_a"],
                "team_b": replay["team_b"],
                "final_score": replay["final_score"],
                "event_count": len(replay.get("events") or []),
            }
            for replay in HISTORICAL_REPLAYS
        ]

    @classmethod
    def get_replay(cls, replay_id: str) -> dict[str, Any] | None:
        for replay in HISTORICAL_REPLAYS:
            if replay.get("id") == replay_id:
                return replay
        return None

    @classmethod
    def build_replay_snapshot(cls, replay_id: str, event_cursor: int = 0) -> dict[str, Any]:
        replay = cls.get_replay(replay_id)
        if not replay:
            raise ValueError("未找到指定的历史回放比赛")

        events = replay.get("events") or []
        cursor = max(0, min(int(event_cursor), len(events)))
        state = _replay_state_template()
        applied_events = []

        for index, event in enumerate(events[:cursor]):
            event_copy = {
                "id": f"{replay_id}-{index}",
                "minute": event.get("minute", 0),
                "team": event.get("team", "team_a"),
                "type": event.get("type", "event"),
                "description": event.get("description", ""),
            }
            applied_events.append(event_copy)
            cls._apply_event(state, event)

        state["events"] = applied_events
        state["minute"] = applied_events[-1]["minute"] if applied_events else 0
        state["notes"] = applied_events[-1]["description"] if applied_events else ""

        current_event = applied_events[-1] if applied_events else None
        next_event = None
        if cursor < len(events):
            upcoming = events[cursor]
            next_event = {
                "id": f"{replay_id}-{cursor}",
                "minute": upcoming.get("minute", 0),
                "team": upcoming.get("team", "team_a"),
                "type": upcoming.get("type", "event"),
                "description": upcoming.get("description", ""),
            }

        return {
            "replay": {
                "id": replay["id"],
                "title": replay["title"],
                "subtitle": replay["subtitle"],
                "competition_name": replay["competition_name"],
                "stage": replay["stage"],
                "team_a": replay["team_a"],
                "team_b": replay["team_b"],
                "final_score": replay["final_score"],
                "event_count": len(events),
            },
            "event_cursor": cursor,
            "current_event": current_event,
            "next_event": next_event,
            "live_state": state,
            "applied_events": applied_events,
        }

    @classmethod
    def _apply_event(cls, state: dict[str, Any], event: dict[str, Any]) -> None:
        side = event.get("team", "team_a")
        is_team_a = side == "team_a"
        event_type = event.get("type")

        if event_type == "goal":
            if is_team_a:
                state["scoreA"] += 1
            else:
                state["scoreB"] += 1
        elif event_type == "red_card":
            if is_team_a:
                state["redCardsA"] += 1
            else:
                state["redCardsB"] += 1
        elif event_type == "yellow_card":
            if is_team_a:
                state["yellowCardsA"] += 1
            else:
                state["yellowCardsB"] += 1
        elif event_type == "injury":
            if is_team_a:
                state["injuriesA"] += 1
            else:
                state["injuriesB"] += 1
        elif event_type == "shot_on_target":
            if is_team_a:
                state["shotsOnTargetA"] += 1
            else:
                state["shotsOnTargetB"] += 1
        elif event_type == "xg_chance":
            if is_team_a:
                state["xgA"] = round(state["xgA"] + 0.3, 2)
            else:
                state["xgB"] = round(state["xgB"] + 0.3, 2)
        elif event_type == "dangerous_attack":
            if is_team_a:
                state["dangerousAttacksA"] += 1
            else:
                state["dangerousAttacksB"] += 1
        elif event_type == "momentum":
            state["momentum"] = side

        effects = event.get("effects") or {}
        state["xgA"] = round(state["xgA"] + float(effects.get("xg_a", 0.0)), 2)
        state["xgB"] = round(state["xgB"] + float(effects.get("xg_b", 0.0)), 2)
        state["shotsOnTargetA"] += int(effects.get("shots_a", 0))
        state["shotsOnTargetB"] += int(effects.get("shots_b", 0))
        state["dangerousAttacksA"] += int(effects.get("dangerous_attacks_a", 0))
        state["dangerousAttacksB"] += int(effects.get("dangerous_attacks_b", 0))
        state["injuriesA"] += int(effects.get("injuries_a", 0))
        state["injuriesB"] += int(effects.get("injuries_b", 0))

        momentum = effects.get("momentum")
        if momentum in {"team_a", "team_b", "balanced"}:
            state["momentum"] = momentum

        state["possessionA"], state["possessionB"] = cls._estimate_possession(state)

    @classmethod
    def _estimate_possession(cls, state: dict[str, Any]) -> tuple[int, int]:
        attack_diff = state["dangerousAttacksA"] - state["dangerousAttacksB"]
        shot_diff = state["shotsOnTargetA"] - state["shotsOnTargetB"]
        raw_shift = attack_diff * 1.5 + shot_diff * 2.0
        if state["momentum"] == "team_a":
            raw_shift += 6
        elif state["momentum"] == "team_b":
            raw_shift -= 6

        shift = max(-18, min(18, int(round(raw_shift))))
        return 50 + shift, 50 - shift

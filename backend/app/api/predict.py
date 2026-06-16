import os
import json
import threading
import hashlib
import re
from pathlib import Path
from flask import request, jsonify
from werkzeug.utils import secure_filename
from . import predict_bp
from ..utils.file_parser import FileParser
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..services.graph_builder import GraphBuilderService
from ..services.historical_replay_service import HistoricalReplayService
from ..services.live_match_data_service import LiveMatchDataService
from ..services.text_processor import TextProcessor
from ..services.zep_tools import ZepToolsService
from ..services.team_data_service import TeamDataService
from ..services.fifa_team_sync import FifaTeamSyncService

logger = get_logger('world_cup.api.predict')

# 球队数据存储目录
TEAMS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../uploads/teams'))
GRAPH_INFO_FILE = os.path.join(TEAMS_DIR, 'graph_info.json')
GRAPH_SEED_DIR = os.path.join(TEAMS_DIR, '.graph_seeded')
GRAPH_TRANSLATION_DIR = os.path.join(TEAMS_DIR, '.graph_translations')

# 确保目录存在
os.makedirs(TEAMS_DIR, exist_ok=True)
os.makedirs(GRAPH_SEED_DIR, exist_ok=True)
os.makedirs(GRAPH_TRANSLATION_DIR, exist_ok=True)

def get_world_cup_graph_id():
    """获取或创建世界杯预测专属图谱"""
    if os.path.exists(GRAPH_INFO_FILE):
        try:
            with open(GRAPH_INFO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('graph_id'):
                    return data['graph_id']
        except Exception as e:
            logger.error(f"读取图谱配置文件失败: {e}")
            
    # 如果不存在，则创建新的全局图谱
    try:
        builder = GraphBuilderService()
        graph_id = builder.create_graph(name="World_Cup_Win_Probability_Graph")
        with open(GRAPH_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump({'graph_id': graph_id}, f)
        logger.info(f"成功创建新的世界杯预测图谱: {graph_id}")
        return graph_id
    except Exception as e:
        logger.error(f"创建图谱失败: {e}")
        return None

def async_add_to_graph(graph_id, text_content):
    """异步将文本分块并添加到Zep图谱中"""
    try:
        logger.info(f"开始将数据上传至Zep图谱: {graph_id}")
        builder = GraphBuilderService()
        # 将长文本切片
        chunks = TextProcessor.split_text(text_content, chunk_size=500, overlap=50)
        # 批量上传
        builder.add_text_batches(graph_id, chunks)
        logger.info(f"成功将 {len(chunks)} 个数据块添加到图谱 {graph_id}")
    except Exception as e:
        logger.error(f"异步添加图谱数据失败: {str(e)}")


def _contains_english(text: str | None) -> bool:
    return bool(text and re.search(r"[A-Za-z]{2,}", text))


def _translation_cache_path(text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return os.path.join(GRAPH_TRANSLATION_DIR, f"{digest}.json")


def _load_cached_translation(text: str) -> str | None:
    path = _translation_cache_path(text)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("translation")
    except Exception:
        return None


def _save_cached_translation(source: str, translation: str) -> None:
    path = _translation_cache_path(source)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"source": source, "translation": translation}, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"缓存翻译失败: {e}")


def _translate_texts_to_chinese(texts: list[str]) -> dict[str, str]:
    pending = []
    translated = {}

    for text in texts:
        if not text:
            continue
        if not _contains_english(text):
            translated[text] = text
            continue
        cached = _load_cached_translation(text)
        if cached:
            translated[text] = cached
        else:
            pending.append(text)

    if not pending:
        return translated

    try:
        llm = LLMClient()
        payload = [{"id": str(i), "text": text} for i, text in enumerate(pending)]
        prompt = (
            "请把下面列表中的英文或中英混合足球摘要翻译成自然流畅的简体中文。\n"
            "要求：\n"
            "1. 保留球队名、球员名、FIFA代码、比分、日期、专有名词。\n"
            "2. 如果原文已经是中文或无需翻译，直接原样返回。\n"
            "3. relation 名称如 HAS_RANKING、PLAYS_ROLE_IN 也要翻成简洁中文短语。\n"
            "4. 只返回 JSON 对象，格式为 {\"items\":[{\"id\":\"0\",\"translation\":\"...\"}]}。\n"
            f"待翻译内容：{json.dumps(payload, ensure_ascii=False)}"
        )
        result = llm.chat_json(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=3000,
        )
        for item in result.get("items", []):
            idx = item.get("id")
            translation = (item.get("translation") or "").strip()
            if idx is None:
                continue
            try:
                source = pending[int(idx)]
            except (ValueError, TypeError, IndexError):
                continue
            final_text = translation or source
            translated[source] = final_text
            _save_cached_translation(source, final_text)
    except Exception as e:
        logger.error(f"图谱摘要翻译失败: {e}")
        for text in pending:
            translated[text] = text

    return translated


def _translate_graph_data(graph_data: dict) -> dict:
    if not graph_data:
        return graph_data

    texts = []
    for node in graph_data.get("nodes", []) or []:
        texts.append(node.get("summary") or "")
    for edge in graph_data.get("edges", []) or []:
        texts.append(edge.get("name") or "")
        texts.append(edge.get("fact") or "")
    for fact in graph_data.get("facts", []) or []:
        texts.append(fact)

    translations = _translate_texts_to_chinese(texts)

    for node in graph_data.get("nodes", []) or []:
        node["summary"] = translations.get(node.get("summary") or "", node.get("summary") or "")
    for edge in graph_data.get("edges", []) or []:
        edge["name"] = translations.get(edge.get("name") or "", edge.get("name") or "")
        edge["fact"] = translations.get(edge.get("fact") or "", edge.get("fact") or "")
    graph_data["facts"] = [translations.get(fact, fact) for fact in (graph_data.get("facts", []) or [])]
    return graph_data


def _safe_int(value, default=0):
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _format_rate(value):
    return f"{round(value * 100, 1)}%"


def _normalize_probabilities(win_a, draw, win_b):
    values = [_clamp(win_a, 0.03, 0.94), _clamp(draw, 0.03, 0.7), _clamp(win_b, 0.03, 0.94)]
    total = sum(values) or 1
    normalized = [value / total for value in values]
    return normalized[0], normalized[1], normalized[2]


def _recent_form_score(team_name):
    team = TeamDataService.get_team(team_name) or {}
    recent_matches = team.get("recent_matches") or []
    score = 0.0
    for match in recent_matches[:5]:
        outcome = (match.get("outcome") or "").upper()
        if "W" in outcome:
            score += 1.0
        elif "D" in outcome:
            score += 0.35
        elif "L" in outcome:
            score -= 0.6
    return score


def _pre_match_baseline(team_a, team_b):
    record_a = TeamDataService.get_team(team_a) or {}
    record_b = TeamDataService.get_team(team_b) or {}
    rank_a = _safe_float((record_a.get("ranking") or {}).get("current_rank"), 60)
    rank_b = _safe_float((record_b.get("ranking") or {}).get("current_rank"), 60)

    rank_advantage = _clamp((rank_b - rank_a) / 120.0, -0.18, 0.18)
    form_advantage = _clamp((_recent_form_score(team_a) - _recent_form_score(team_b)) * 0.04, -0.12, 0.12)

    win_a = 0.38 + rank_advantage + form_advantage
    win_b = 0.38 - rank_advantage - form_advantage
    draw = 0.24 - abs(rank_advantage) * 0.35 - abs(form_advantage) * 0.2
    return _normalize_probabilities(win_a, draw, win_b)


def _rate_delta_text(current_rate, baseline_rate):
    diff = round((current_rate - baseline_rate) * 100, 1)
    if diff > 0:
        return f"+{diff}%"
    return f"{diff}%"


def _event_team_label(side, team_a, team_b):
    return team_a if side == "team_a" else team_b


def _event_type_label(event_type):
    mapping = {
        "goal": "进球",
        "red_card": "红牌",
        "yellow_card": "黄牌",
        "injury": "伤病",
        "shot_on_target": "射正",
        "dangerous_attack": "危险进攻",
        "xg_chance": "高质量机会",
        "momentum": "势头变化",
    }
    return mapping.get(event_type, event_type or "事件")


def _summarize_live_events(events, team_a, team_b):
    items = []
    for event in events or []:
        minute = _safe_int(event.get("minute"), 0)
        side = event.get("team") or "team_a"
        team_label = _event_team_label(side, team_a, team_b)
        event_type = _event_type_label(event.get("type"))
        description = (event.get("description") or "").strip()
        text = f"第 {minute} 分钟，{team_label}{event_type}"
        if description:
            text += f"：{description[:50]}"
        items.append({
            "minute": minute,
            "text": text,
        })
    items.sort(key=lambda item: item["minute"], reverse=True)
    return items


def _build_live_prediction(team_a, team_b, live_state, factors=""):
    base_a, base_draw, base_b = _pre_match_baseline(team_a, team_b)
    win_a, draw, win_b = base_a, base_draw, base_b
    key_impacts = []
    event_summaries = _summarize_live_events(live_state.get("events") or [], team_a, team_b)

    minute = _clamp(_safe_int(live_state.get("minute"), 0), 0, 130)
    score_a = _safe_int(live_state.get("scoreA", live_state.get("score_a")), 0)
    score_b = _safe_int(live_state.get("scoreB", live_state.get("score_b")), 0)
    red_a = _safe_int(live_state.get("redCardsA", live_state.get("red_cards_a")), 0)
    red_b = _safe_int(live_state.get("redCardsB", live_state.get("red_cards_b")), 0)
    yellow_a = _safe_int(live_state.get("yellowCardsA", live_state.get("yellow_cards_a")), 0)
    yellow_b = _safe_int(live_state.get("yellowCardsB", live_state.get("yellow_cards_b")), 0)
    injuries_a = _safe_int(live_state.get("injuriesA", live_state.get("injuries_a")), 0)
    injuries_b = _safe_int(live_state.get("injuriesB", live_state.get("injuries_b")), 0)
    shots_a = _safe_int(live_state.get("shotsOnTargetA", live_state.get("shots_on_target_a")), 0)
    shots_b = _safe_int(live_state.get("shotsOnTargetB", live_state.get("shots_on_target_b")), 0)
    dangerous_a = _safe_int(live_state.get("dangerousAttacksA", live_state.get("dangerous_attacks_a")), 0)
    dangerous_b = _safe_int(live_state.get("dangerousAttacksB", live_state.get("dangerous_attacks_b")), 0)
    xg_a = _safe_float(live_state.get("xgA", live_state.get("xg_a")), 0.0)
    xg_b = _safe_float(live_state.get("xgB", live_state.get("xg_b")), 0.0)
    possession_a = _safe_float(live_state.get("possessionA", live_state.get("possession_a")), 50.0)
    possession_b = _safe_float(live_state.get("possessionB", live_state.get("possession_b")), 50.0)

    if possession_a <= 0 and possession_b > 0:
        possession_a = 100 - possession_b
    if possession_b <= 0 and possession_a > 0:
        possession_b = 100 - possession_a

    time_factor = _clamp(minute / 90.0, 0.0, 1.25)
    score_diff = score_a - score_b
    if score_diff != 0:
        score_swing = abs(score_diff) * (0.2 + 0.34 * time_factor)
        if score_diff > 0:
            win_a += score_swing
            win_b -= score_swing * 0.8
            draw -= 0.08 + 0.12 * time_factor
            key_impacts.append((score_swing, f"{team_a}目前以 {score_a}:{score_b} 领先，比分优势正在放大胜率。"))
        else:
            win_b += score_swing
            win_a -= score_swing * 0.8
            draw -= 0.08 + 0.12 * time_factor
            key_impacts.append((score_swing, f"{team_b}目前以 {score_b}:{score_a} 领先，实时概率明显向客队倾斜。"))
    else:
        draw += 0.06 + 0.08 * time_factor
        key_impacts.append((0.08, f"比赛进行到第 {minute} 分钟仍然打平，平局概率被阶段性抬高。"))

    red_diff = red_b - red_a
    if red_diff:
        red_swing = abs(red_diff) * 0.22
        if red_diff > 0:
            win_a += red_swing
            win_b -= red_swing * 0.9
            draw -= 0.04
            key_impacts.append((red_swing, f"{team_b}红牌更多，人数劣势显著拉低了他们的胜率。"))
        else:
            win_b += red_swing
            win_a -= red_swing * 0.9
            draw -= 0.04
            key_impacts.append((red_swing, f"{team_a}红牌更多，人数劣势明显影响比赛走势。"))

    yellow_diff = yellow_b - yellow_a
    if yellow_diff:
        yellow_swing = min(abs(yellow_diff) * 0.02, 0.06)
        if yellow_diff > 0:
            win_a += yellow_swing
            win_b -= yellow_swing
            key_impacts.append((yellow_swing, f"{team_b}黄牌更多，防守动作和后续红牌风险更高。"))
        else:
            win_b += yellow_swing
            win_a -= yellow_swing
            key_impacts.append((yellow_swing, f"{team_a}黄牌更多，比赛控制力受到一定牵制。"))

    xg_diff = _clamp(xg_a - xg_b, -3.0, 3.0)
    if abs(xg_diff) >= 0.15:
        xg_swing = min(abs(xg_diff) * 0.12, 0.18)
        if xg_diff > 0:
            win_a += xg_swing
            win_b -= xg_swing * 0.75
            key_impacts.append((xg_swing, f"{team_a}当前 xG 更高，说明制造高质量机会的能力更强。"))
        else:
            win_b += xg_swing
            win_a -= xg_swing * 0.75
            key_impacts.append((xg_swing, f"{team_b}当前 xG 更高，比赛内容上更接近下一粒进球。"))

    shots_diff = _clamp(shots_a - shots_b, -8, 8)
    if shots_diff:
        shot_swing = min(abs(shots_diff) * 0.025, 0.12)
        if shots_diff > 0:
            win_a += shot_swing
            win_b -= shot_swing * 0.8
            key_impacts.append((shot_swing, f"{team_a}射正更多，持续给对手防线施压。"))
        else:
            win_b += shot_swing
            win_a -= shot_swing * 0.8
            key_impacts.append((shot_swing, f"{team_b}射正更多，门前威胁更连续。"))

    possession_diff = _clamp((possession_a - possession_b) / 100.0, -0.45, 0.45)
    if abs(possession_diff) >= 0.04:
        possession_swing = abs(possession_diff) * 0.16
        if possession_diff > 0:
            win_a += possession_swing
            win_b -= possession_swing * 0.65
            key_impacts.append((possession_swing, f"{team_a}控球占优，比赛节奏更多掌握在主队脚下。"))
        else:
            win_b += possession_swing
            win_a -= possession_swing * 0.65
            key_impacts.append((possession_swing, f"{team_b}控球占优，整体推进更从容。"))

    danger_diff = _clamp(dangerous_a - dangerous_b, -40, 40)
    if danger_diff:
        danger_swing = min(abs(danger_diff) * 0.004, 0.1)
        if danger_diff > 0:
            win_a += danger_swing
            win_b -= danger_swing * 0.75
            key_impacts.append((danger_swing, f"{team_a}危险进攻次数更多，进球预兆更活跃。"))
        else:
            win_b += danger_swing
            win_a -= danger_swing * 0.75
            key_impacts.append((danger_swing, f"{team_b}危险进攻次数更多，压制力更明显。"))

    injury_diff = injuries_b - injuries_a
    if injury_diff:
        injury_swing = min(abs(injury_diff) * 0.07, 0.18)
        if injury_diff > 0:
            win_a += injury_swing
            win_b -= injury_swing
            key_impacts.append((injury_swing, f"{team_b}伤病或被动调整更多，阵容完整性受到影响。"))
        else:
            win_b += injury_swing
            win_a -= injury_swing
            key_impacts.append((injury_swing, f"{team_a}伤病或被动调整更多，执行力有所下降。"))

    momentum = live_state.get("momentum") or ""
    if momentum == "team_a":
        win_a += 0.06
        win_b -= 0.04
        key_impacts.append((0.06, f"最近阶段场面势头更偏向 {team_a}。"))
    elif momentum == "team_b":
        win_b += 0.06
        win_a -= 0.04
        key_impacts.append((0.06, f"最近阶段场面势头更偏向 {team_b}。"))

    if score_diff == 0 and minute >= 75:
        draw += 0.08
    elif abs(score_diff) == 1 and minute >= 75:
        if score_diff > 0:
            win_a += 0.06
            draw -= 0.02
        else:
            win_b += 0.06
            draw -= 0.02

    notes = (live_state.get("notes") or factors or "").strip()
    if notes:
        key_impacts.append((0.04, f"补充赛况：{notes[:80]}"))
    for index, event in enumerate(event_summaries[:2]):
        key_impacts.append((0.05 - index * 0.01, f"最近关键事件：{event['text']}"))

    win_a, draw, win_b = _normalize_probabilities(win_a, draw, win_b)
    sorted_impacts = sorted(key_impacts, key=lambda item: item[0], reverse=True)
    top_factors = [text for _, text in sorted_impacts[:4]]

    if win_a >= win_b and win_a >= draw:
        trend = f"{team_a}占优"
    elif win_b >= win_a and win_b >= draw:
        trend = f"{team_b}占优"
    else:
        trend = "平局趋势增强"

    summary = (
        f"第 {minute} 分钟，场上比分 {team_a} {score_a}:{score_b} {team_b}。"
        f" 当前模型判断为“{trend}”，胜率变化主要受比分、人数与场面数据共同驱动。"
    )
    if event_summaries:
        summary += f" 最近的关键节点是：{event_summaries[0]['text']}。"

    return {
        "mode": "live",
        "minute": minute,
        "scoreline": f"{team_a} {score_a}:{score_b} {team_b}",
        "win_rate_a": _format_rate(win_a),
        "draw_rate": _format_rate(draw),
        "win_rate_b": _format_rate(win_b),
        "baseline_win_rate_a": _format_rate(base_a),
        "baseline_draw_rate": _format_rate(base_draw),
        "baseline_win_rate_b": _format_rate(base_b),
        "delta_win_rate_a": _rate_delta_text(win_a, base_a),
        "delta_draw_rate": _rate_delta_text(draw, base_draw),
        "delta_win_rate_b": _rate_delta_text(win_b, base_b),
        "live_summary": summary,
        "tactical_analysis": summary,
        "key_factors": top_factors or ["当前没有足够的实时事件输入，系统主要沿用赛前基线概率。"],
        "final_prediction": f"{trend}，建议结合后续 5-10 分钟内的关键事件继续刷新判断。",
        "momentum_label": trend,
        "events_note": notes,
        "event_count": len(event_summaries),
        "recent_events": [item["text"] for item in event_summaries[:5]],
    }


def _normalize_live_source_payload(match_detail, factors=""):
    live_state = match_detail.get("live_state") or {}
    team_a = match_detail.get("home_team_cn") or match_detail.get("home_team")
    team_b = match_detail.get("away_team_cn") or match_detail.get("away_team")
    prediction = _build_live_prediction(team_a, team_b, live_state, factors)
    return {
        "team_a": team_a,
        "team_b": team_b,
        "match": match_detail,
        "prediction": prediction,
    }


def _build_historical_replay_payload(snapshot, factors=""):
    replay = snapshot.get("replay") or {}
    team_a = replay.get("team_a") or ""
    team_b = replay.get("team_b") or ""
    live_state = snapshot.get("live_state") or {}
    prediction = _build_live_prediction(team_a, team_b, live_state, factors)
    return {
        "replay": replay,
        "team_a": team_a,
        "team_b": team_b,
        "event_cursor": snapshot.get("event_cursor", 0),
        "current_event": snapshot.get("current_event"),
        "next_event": snapshot.get("next_event"),
        "live_state": live_state,
        "applied_events": snapshot.get("applied_events") or [],
        "prediction": prediction,
    }

@predict_bp.route('/upload', methods=['POST'])
def upload_team_data():
    """
    上传球队数据文件
    支持 txt, md, pdf 格式，将其解析后保存为 球队名.txt
    """
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "没有找到上传的文件"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "未选择文件"}), 400
            
        # 提取球队名 (假设文件名即球队名，比如 '阿根廷.txt' -> '阿根廷')
        original_filename = secure_filename(file.filename) if file.filename.isascii() else file.filename
        team_name = os.path.splitext(original_filename)[0]
        
        # 临时保存文件以供解析
        temp_path = os.path.join(TEAMS_DIR, f"temp_{original_filename}")
        file.save(temp_path)
        
        try:
            # 提取文本内容
            text_content = FileParser.extract_text(temp_path)
            
            # 智能提取球队真实名称
            llm = LLMClient()
            team_extract_prompt = f"""
请分析以下文件名和文本内容，判断这份资料属于哪支参加世界杯的【国家队】。
文件名：{original_filename}
文本开头内容：{text_content[:500]}

请只输出这支国家队的标准中文名称（例如：阿根廷、法国、巴西、英格兰等）。不要输出任何多余的解释、标点或换行。如果无法判断，请直接输出原文件名去掉后缀。
"""
            extracted_team_name = llm.chat(
                messages=[{"role": "user", "content": team_extract_prompt}],
                temperature=0.1,
                max_tokens=20
            ).strip()
            
            # 如果提取出来的名字包含标点或特殊字符，或者包含“无法判断”，说明提取失败
            import re
            if not extracted_team_name or len(extracted_team_name) > 20 or re.search(r'[^\w\u4e00-\u9fa5]', extracted_team_name) or "无法" in extracted_team_name:
                os.remove(temp_path)
                return jsonify({"success": False, "error": f"未能从文件 '{original_filename}' 中识别出有效的球队名称"}), 400
            
            team_name = extracted_team_name

        except Exception as e:
            os.remove(temp_path)
            return jsonify({"success": False, "error": f"解析文件失败: {str(e)}"}), 400
            
        # 保存为标准的txt文件（如果已存在则追加内容）
        final_path = os.path.join(TEAMS_DIR, f"{team_name}.txt")
        mode = 'a' if os.path.exists(final_path) else 'w'
        
        with open(final_path, mode, encoding='utf-8') as f:
            if mode == 'a':
                f.write("\n\n=== 新增补充资料 ===\n\n")
            f.write(text_content)

        TeamDataService.ensure_uploaded_team_entry(team_name)
            
        # 异步启动图谱构建（为了不阻塞前端上传的响应时间）
        graph_id = get_world_cup_graph_id()
        if graph_id:
            threading.Thread(target=async_add_to_graph, args=(graph_id, text_content), daemon=True).start()
            
        # 删除临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify({
            "success": True, 
            "data": {
                "team_name": team_name,
                "message": "球队数据上传成功"
            }
        })
        
    except Exception as e:
        logger.error(f"上传球队数据失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/teams', methods=['GET'])
def get_teams():
    """获取已上传的球队列表"""
    try:
        scope = request.args.get('scope')
        if scope == 'all':
            teams = set(TeamDataService.get_all_teams())
        else:
            teams = set(TeamDataService.get_world_cup_2026_teams())
        if os.path.exists(TEAMS_DIR):
            for filename in os.listdir(TEAMS_DIR):
                if filename.endswith('.txt') and not filename.startswith('temp_'):
                    team_name = filename[:-4]
                    if scope == 'all':
                        teams.add(team_name)
                    
        return jsonify({
            "success": True,
            "data": {
                "teams": sorted(teams)
            }
        })
    except Exception as e:
        logger.error(f"获取球队列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/team/<team_name>', methods=['GET'])
def get_team_detail(team_name):
    """
    获取指定球队的图谱详细信息
    返回节点、边、以及总结事实
    """
    try:
        structured_data = TeamDataService.get_team(team_name)
        structured_text = TeamDataService.build_team_analysis_text(team_name)
        graph_seed_text = TeamDataService.build_graph_seed_text(team_name)
        graph_id = get_world_cup_graph_id()
        filtered_nodes = []
        filtered_edges = []
        filtered_facts = []
        query = f"{team_name}国家队"
        seeded = False
        tokens = set(TeamDataService.get_team_identity_tokens(team_name) or [team_name])

        if graph_id:
            zep_tools = ZepToolsService()
            
            # 使用图谱搜索查询该球队的全貌信息
            search_result = zep_tools.search_graph(graph_id, query, limit=50)
            
            # 强制本地过滤：确保返回的图谱信息中包含当前球队名，避免语义泛化混入其他球队数据
            raw_nodes = getattr(search_result, "nodes", None) or []
            raw_edges = getattr(search_result, "edges", None) or []
            raw_facts = getattr(search_result, "facts", None) or []

            if raw_nodes:
                for node in raw_nodes:
                    node_text = f"{node.get('name', '')} {node.get('summary', '')}"
                    if any(token in node_text for token in tokens):
                        filtered_nodes.append(node)
                        
            if raw_edges:
                for edge in raw_edges:
                    edge_text = f"{edge.get('name', '')} {edge.get('fact', '')}"
                    if any(token in edge_text for token in tokens):
                        filtered_edges.append(edge)
                        
            if raw_facts:
                for fact in raw_facts:
                    if any(token in fact for token in tokens):
                        filtered_facts.append(fact)

            if not filtered_nodes and not filtered_edges and not filtered_facts and graph_seed_text:
                marker = Path(os.path.join(GRAPH_SEED_DIR, f"{team_name}_v2.json"))
                if not marker.exists():
                    marker.write_text(json.dumps({"seeded": True, "version": 2}, ensure_ascii=False), encoding="utf-8")
                    threading.Thread(target=async_add_to_graph, args=(graph_id, graph_seed_text), daemon=True).start()
                    seeded = True
                    
        # 组装过滤后的数据
        graph_data = {
            "nodes": filtered_nodes,
            "edges": filtered_edges,
            "facts": filtered_facts,
            "query": query,
            "total_count": len(filtered_facts)
        }
        graph_data = _translate_graph_data(graph_data)
        
        # 尝试读取本地文本作为补充
        local_text = ""
        path = os.path.join(TEAMS_DIR, f"{team_name}.txt")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                local_text = f.read()

        return jsonify({
            "success": True,
            "data": {
                "team_name": team_name,
                "graph_data": graph_data,
                "local_text": local_text,
                "structured_data": structured_data,
                "structured_text": structured_text,
                "graph_seeded": seeded
            }
        })
    except Exception as e:
        logger.error(f"获取球队图谱详情失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/sync-fifa', methods=['POST'])
def sync_fifa_teams():
    """同步 FIFA 官方球队结构化数据。"""
    try:
        data = request.get_json(silent=True) or {}
        team_names = data.get('teamNames')
        team_codes = data.get('teamCodes')
        scope = data.get('scope')
        result = FifaTeamSyncService.sync_teams(team_names=team_names, team_codes=team_codes, scope=scope)
        return jsonify({
            "success": True,
            "data": result,
        })
    except Exception as e:
        logger.error(f"同步 FIFA 数据失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@predict_bp.route('/analyze', methods=['POST'])
def analyze_match():
    """
    分析比赛胜率
    接收：team_a, team_b, factors (特殊因素)
    返回JSON：主队胜率，客队胜率，平局概率，战术分析，最终预测
    """
    try:
        data = request.get_json() or {}
        team_a = data.get('teamA')
        team_b = data.get('teamB')
        factors = data.get('factors', '')
        
        if not team_a or not team_b:
            return jsonify({"success": False, "error": "请选择主队和客队"}), 400
            
        # 读取球队数据 (提供两种维度的情报：Zep图谱检索 + 本地部分摘要兜底)
        def get_team_info(name):
            graph_info_lines = []
            structured_summary = TeamDataService.build_team_analysis_text(name)
            graph_id = get_world_cup_graph_id()
            
            # 1. 尝试从Zep图谱中深度检索情报
            if graph_id:
                try:
                    zep_tools = ZepToolsService()
                    # 针对世界杯的精准提问，触发混合搜索
                    query = f"{name}国家队的战术打法、核心阵容、主教练风格、伤病情况与近期比赛状态"
                    # 这里调用我们原有的 search_graph 工具
                    search_result = zep_tools.search_graph(graph_id, query, limit=15)
                    
                    if hasattr(search_result, 'facts') and search_result.facts:
                        graph_info_lines.extend([f"- {fact}" for fact in search_result.facts])
                except Exception as e:
                    logger.error(f"检索图谱失败: {e}")

            # 2. 从本地读取前1000字作为基础背景兜底（因为图谱处理需要时间，可能刚上传就预测）
            local_text = ""
            path = os.path.join(TEAMS_DIR, f"{name}.txt")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    local_text = f.read()[:1000]  # 限制长度以控制Token
                    
            if not graph_info_lines and not local_text:
                if structured_summary:
                    return structured_summary
                return f"暂无【{name}】的详细数据，请根据常识和模型知识进行分析。"
                
            # 综合两方面数据
            final_info = ""
            if structured_summary:
                final_info += structured_summary + "\n\n"
            if graph_info_lines:
                final_info += f"【Zep图谱深度分析与核心关联】：\n" + "\n".join(graph_info_lines) + "\n\n"
            if local_text:
                final_info += f"【原始背景资料摘要】：\n{local_text}"
                
            return final_info
            
        info_a = get_team_info(team_a)
        info_b = get_team_info(team_b)
        
        # 构建大模型 Prompt
        system_prompt = "你是一个专业的世界杯足球赛事预测专家。请根据提供的球队历史数据、现状以及用户提供的特殊因素，客观、深度地分析两支球队的胜率。"
        
        user_prompt = f"""
请预测以下两支球队的比赛结果：
主队：{team_a}
客队：{team_b}

【主队（{team_a}）近期数据/信息】：
{info_a[:2000]} # 限制长度避免超出上下文

【客队（{team_b}）近期数据/信息】：
{info_b[:2000]}

【特殊因素/附加说明】：
{factors if factors else '无'}

请仔细分析两队的综合实力、战术克制关系、伤病及特殊因素，并以JSON格式返回预测结果。返回的JSON必须包含以下字段：
- win_rate_a: 主队({team_a})胜率（如 45%）
- win_rate_b: 客队({team_b})胜率（如 35%）
- draw_rate: 平局概率（如 20%）（三个概率相加需为100%）
- tactical_analysis: 战术分析（一段详细的文字，分析双方优劣势及战术克制）
- key_factors: 关键胜负手（列出影响比赛结果的3个关键点，列表格式）
- final_prediction: 最终预测结论（如“阿根廷 2:1 法国，阿根廷小胜”）
"""
        
        llm = LLMClient()
        result_json = llm.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4
        )
        
        return jsonify({
            "success": True,
            "data": result_json
        })
        
    except Exception as e:
        logger.error(f"预测分析失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/live-analyze', methods=['POST'])
def analyze_live_match():
    """
    比赛进行中的动态胜率预测
    接收：teamA, teamB, factors, liveState
    返回：实时主胜/平/客胜概率及变化原因
    """
    try:
        data = request.get_json() or {}
        team_a = data.get('teamA')
        team_b = data.get('teamB')
        live_state = data.get('liveState') or {}
        factors = data.get('factors', '')

        if not team_a or not team_b:
            return jsonify({"success": False, "error": "请选择主队和客队"}), 400

        result = _build_live_prediction(team_a, team_b, live_state, factors)
        return jsonify({
            "success": True,
            "data": result,
        })
    except Exception as e:
        logger.error(f"动态预测分析失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/live-source/providers', methods=['GET'])
def get_live_source_providers():
    try:
        return jsonify({
            "success": True,
            "data": {
                "default_provider": os.environ.get('LIVE_DATA_PROVIDER', 'football-data'),
                "poll_interval_seconds": int(os.environ.get('LIVE_DATA_POLL_INTERVAL_SECONDS', '30')),
                "providers": LiveMatchDataService.get_provider_options(),
            },
        })
    except Exception as e:
        logger.error(f"获取直播数据源配置失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/live-source/matches', methods=['GET'])
def get_live_source_matches():
    try:
        provider = request.args.get('provider')
        date = request.args.get('date')
        live_only = request.args.get('live_only', 'true').lower() == 'true'
        matches = LiveMatchDataService.get_live_matches(provider_name=provider, date=date, live_only=live_only)
        return jsonify({
            "success": True,
            "data": {
                "matches": matches,
            },
        })
    except Exception as e:
        logger.error(f"获取直播比赛列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/live-source/analyze', methods=['POST'])
def analyze_live_source_match():
    try:
        data = request.get_json() or {}
        provider = data.get('provider')
        fixture_id = data.get('fixtureId') or data.get('fixture_id')
        factors = data.get('factors', '')

        if not fixture_id:
            return jsonify({"success": False, "error": "请提供直播比赛 fixtureId"}), 400

        match_detail = LiveMatchDataService.get_live_match_detail(fixture_id=fixture_id, provider_name=provider)
        result = _normalize_live_source_payload(match_detail, factors=factors)
        return jsonify({
            "success": True,
            "data": result,
        })
    except Exception as e:
        logger.error(f"直播数据源动态预测失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/live-source/auto-analyze', methods=['POST'])
def analyze_auto_selected_live_source_match():
    try:
        data = request.get_json() or {}
        provider = data.get('provider')
        team_a = data.get('teamA') or data.get('team_a')
        team_b = data.get('teamB') or data.get('team_b')
        date = data.get('date')
        live_only = data.get('liveOnly', True)
        factors = data.get('factors', '')

        match_summary = LiveMatchDataService.find_best_live_match(
            provider_name=provider,
            team_a=team_a,
            team_b=team_b,
            date=date,
            live_only=bool(live_only),
        )
        if not match_summary:
            return jsonify({"success": False, "error": "当前没有可自动匹配的直播世界杯比赛"}), 404

        match_detail = LiveMatchDataService.get_live_match_detail(
            fixture_id=match_summary.get('fixture_id'),
            provider_name=provider,
        )
        result = _normalize_live_source_payload(match_detail, factors=factors)
        result["matched_fixture"] = match_summary
        result["auto_selected"] = True
        return jsonify({
            "success": True,
            "data": result,
        })
    except Exception as e:
        logger.error(f"自动选择直播比赛并预测失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/historical-replays', methods=['GET'])
def get_historical_replays():
    try:
        return jsonify({
            "success": True,
            "data": {
                "replays": HistoricalReplayService.list_replays(),
            },
        })
    except Exception as e:
        logger.error(f"获取历史回放列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@predict_bp.route('/historical-replays/analyze', methods=['POST'])
def analyze_historical_replay():
    try:
        data = request.get_json() or {}
        replay_id = data.get('replayId') or data.get('replay_id')
        event_cursor = data.get('eventCursor', 0)
        factors = data.get('factors', '')

        if not replay_id:
            return jsonify({"success": False, "error": "请先选择一场历史回放比赛"}), 400

        snapshot = HistoricalReplayService.build_replay_snapshot(
            replay_id=replay_id,
            event_cursor=event_cursor,
        )
        result = _build_historical_replay_payload(snapshot, factors=factors)
        return jsonify({
            "success": True,
            "data": result,
        })
    except Exception as e:
        logger.error(f"历史回放动态预测失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

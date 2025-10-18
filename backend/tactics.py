"""Endpoints focused on Flames of War tactical tooling."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.ai_clients import AIProviderError, MissingConfigurationError, generate_ai_response
from backend.extensions import limiter
from backend.models import BattleLog, db


tactics_bp = Blueprint("tactics", __name__)


def _tactics_limit() -> str:
    return current_app.config.get("TACTICS_RATE_LIMIT", "20/minute")


def _validate_units(units: Any) -> List[Dict[str, Any]]:
    if not isinstance(units, list):
        raise ValueError("Units must be an array.")
    validated: List[Dict[str, Any]] = []
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("Each unit must be an object.")
        name = (unit.get("name") or "").strip()
        role = (unit.get("role") or "").strip()
        strength = unit.get("strength", "")
        validated.append({"name": name, "role": role, "strength": strength})
    return validated


def _call_ai(prompt: str, provider: str | None = None) -> str:
    config = current_app.config
    chosen_provider = provider or config.get("DEFAULT_AI_PROVIDER", "openai")
    return generate_ai_response(prompt, chosen_provider, config)


def _build_scenario_prompt(state: Dict[str, Any]) -> str:
    turn = state.get("turn")
    player = state.get("player")
    objective = state.get("objective")
    enemy = state.get("enemyDisposition")
    weather = state.get("weather")
    terrain = state.get("terrain")
    units = _validate_units(state.get("units", []))

    lines = [
        "You are an experienced Flames of War commander offering tactical advice.",
        "Analyse the following battle snapshot and respond with concrete recommendations.",
        f"Turn: {turn}",
        f"Player: {player}",
        f"Objective: {objective}",
        f"Enemy disposition: {enemy}",
        f"Weather: {weather}",
        f"Terrain notes: {terrain}",
        "Friendly units:",
    ]
    for unit in units:
        lines.append(
            f"- {unit['name']} ({unit['role']}) strength:{unit['strength']}"
        )
    lines.append(
        "Provide three actionable suggestions, highlight immediate threats, and propose a risk mitigation plan."
    )
    return "\n".join(lines)


def _build_army_prompt(list_payload: Dict[str, Any]) -> str:
    faction = list_payload.get("faction", "Unknown")
    points = list_payload.get("points")
    units = _validate_units(list_payload.get("units", []))
    lines = [
        "You are reviewing a Flames of War army list.",
        f"Faction: {faction}",
        f"Total points: {points}",
        "Provide feedback on synergy, mobility, anti-tank coverage, and morale tools.",
        "Suggested improvements should include at least one unit swap and one tactical consideration.",
        "Army composition:",
    ]
    for unit in units:
        lines.append(f"- {unit['name']} ({unit['role']}) strength:{unit['strength']}")
    return "\n".join(lines)


def _build_coach_prompt(payload: Dict[str, Any]) -> str:
    role = (payload.get("role") or current_app.config.get("DEFAULT_SCENARIO_ROLE", "battlefield analyst")).strip()
    focus = payload.get("focus", "")
    player_goal = payload.get("goal", "")
    message = payload.get("message", "")
    return (
        "Act as a {role} mentoring a Flames of War commander.\n"
        "Strategic focus: {focus}\n"
        "Player goal: {goal}\n"
        "Player input: {message}\n"
        "Respond with encouragement, two tactical priorities, and a cautionary note."
    ).format(role=role, focus=focus, goal=player_goal, message=message)


@tactics_bp.route("/scenario-advice", methods=["POST"])
@jwt_required()
@limiter.limit(_tactics_limit)
def scenario_advice():
    payload = request.get_json(silent=True) or {}
    battle_state = payload.get("battleState") or {}
    if not isinstance(battle_state, dict):
        return jsonify({"error": "battleState must be an object."}), 400

    try:
        prompt = _build_scenario_prompt(battle_state)
        response = _call_ai(prompt, payload.get("provider"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except MissingConfigurationError as exc:
        return jsonify({"error": str(exc)}), 400
    except AIProviderError as exc:  # pragma: no cover - network failure path
        current_app.logger.warning("Scenario advice provider error", extra={"provider_error": str(exc)})
        return jsonify({"error": str(exc)}), getattr(exc, "status_code", 502)

    return jsonify({"analysis": response})


@tactics_bp.route("/army-list", methods=["POST"])
@jwt_required()
@limiter.limit(_tactics_limit)
def army_list():
    payload = request.get_json(silent=True) or {}
    try:
        prompt = _build_army_prompt(payload)
        response = _call_ai(prompt, payload.get("provider"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except MissingConfigurationError as exc:
        return jsonify({"error": str(exc)}), 400
    except AIProviderError as exc:  # pragma: no cover - network failure path
        current_app.logger.warning("Army list provider error", extra={"provider_error": str(exc)})
        return jsonify({"error": str(exc)}), getattr(exc, "status_code", 502)

    return jsonify({"analysis": response})


@tactics_bp.route("/coach", methods=["POST"])
@jwt_required()
@limiter.limit(_tactics_limit)
def coach():
    payload = request.get_json(silent=True) or {}
    try:
        prompt = _build_coach_prompt(payload)
        response = _call_ai(prompt, payload.get("provider"))
    except MissingConfigurationError as exc:
        return jsonify({"error": str(exc)}), 400
    except AIProviderError as exc:  # pragma: no cover - network failure path
        current_app.logger.warning("Coach provider error", extra={"provider_error": str(exc)})
        return jsonify({"error": str(exc)}), getattr(exc, "status_code", 502)

    return jsonify({"coaching": response})


@tactics_bp.route("/logs", methods=["POST"])
@jwt_required()
@limiter.limit(_tactics_limit)
def create_log():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip() or "Untitled engagement"
    scenario = (payload.get("scenario") or "").strip()
    entries = payload.get("entries") or []
    if not isinstance(entries, list):
        return jsonify({"error": "Entries must be an array."}), 400

    user_id = get_jwt_identity()
    log = BattleLog(user_id=user_id, title=title, scenario=scenario, entries=entries)
    db.session.add(log)
    db.session.commit()

    return jsonify({"id": log.id, "createdAt": log.created_at.isoformat()}), 201


@tactics_bp.route("/logs", methods=["GET"])
@jwt_required()
def list_logs():
    user_id = get_jwt_identity()
    logs = (
        BattleLog.query.filter_by(user_id=user_id)
        .order_by(BattleLog.created_at.desc())
        .limit(50)
        .all()
    )
    serialized = [
        {
            "id": log.id,
            "title": log.title,
            "scenario": log.scenario,
            "createdAt": log.created_at.isoformat(),
            "entries": log.entries,
        }
        for log in logs
    ]
    return jsonify({"logs": serialized})


@tactics_bp.route("/logs/<int:log_id>", methods=["DELETE"])
@jwt_required()
def delete_log(log_id: int):
    user_id = get_jwt_identity()
    log = BattleLog.query.filter_by(id=log_id, user_id=user_id).first()
    if not log:
        return jsonify({"message": "Log not found."}), 404

    db.session.delete(log)
    db.session.commit()
    return jsonify({"message": "Log deleted."})

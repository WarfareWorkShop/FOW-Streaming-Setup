"""Game mechanics for the Flames of War assistant."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple


@dataclass
class GameRuleError(ValueError):
    """Raised when a player attempts an invalid action."""

    message: str


def initial_state(scenario: str | None = None) -> Dict[str, Any]:
    """Return the initial match state for the provided scenario."""

    battlefield = scenario or "Encuentro estándar"
    return {
        "round": 1,
        "battlefield": battlefield,
        "turn": "player",
        "player": {"units": 6, "morale": 10, "victory_points": 0},
        "ai": {"units": 6, "morale": 10, "victory_points": 0},
        "log": [
            {
                "actor": "system",
                "text": f"La batalla comienza en el escenario '{battlefield}'.",
            }
        ],
    }


def _clamp(value: int, *, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _resolve_damage(intensity: int, defense: int) -> Tuple[int, str]:
    net = intensity - defense
    if net <= 0:
        return 0, "La defensa absorbe el ataque."
    if net == 1:
        return 1, "El ataque logra abrir una brecha leve."
    return _clamp(net, minimum=1, maximum=3), "Impacto directo sobre las unidades enemigas."


def _append_log(state: Dict[str, Any], actor: str, text: str) -> None:
    state.setdefault("log", []).append({"actor": actor, "text": text})


def _advance_round(state: Dict[str, Any]) -> None:
    state["round"] = int(state.get("round", 1)) + 1


def _maybe_end_match(state: Dict[str, Any]) -> None:
    if state["player"]["units"] <= 0 and state["ai"]["units"] <= 0:
        _append_log(
            state,
            "system",
            "Ambos pelotones quedan inutilizados. La batalla termina en empate.",
        )
        state["turn"] = "completed"
    elif state["ai"]["units"] <= 0:
        _append_log(state, "system", "¡Victoria aliada! El oponente se retira.")
        state["turn"] = "completed"
    elif state["player"]["units"] <= 0:
        _append_log(state, "system", "La ofensiva enemiga prevalece. Has sido derrotado.")
        state["turn"] = "completed"


def apply_player_action(state: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a player action to the match state."""

    if state.get("turn") != "player":
        raise GameRuleError("No es tu turno actualmente.")

    action_type = (action.get("type") or "").lower()
    if action_type not in {"attack", "defend", "regroup", "recon"}:
        raise GameRuleError("La acción solicitada no es válida.")

    intensity = _clamp(int(action.get("intensity", 2)), minimum=1, maximum=5)
    support = _clamp(int(action.get("support", 0)), minimum=0, maximum=3)
    defence_bonus = 0

    if action_type == "attack":
        damage, narrative = _resolve_damage(intensity + support, defense=2)
        state["ai"]["units"] = max(0, state["ai"]["units"] - damage)
        state["player"]["victory_points"] += damage
        _append_log(
            state,
            "player",
            f"Ordenas un ataque con intensidad {intensity} y apoyo {support}. {narrative}",
        )
    elif action_type == "defend":
        defence_bonus = intensity
        state["player"]["morale"] = _clamp(
            state["player"].get("morale", 10) + 1,
            minimum=0,
            maximum=12,
        )
        _append_log(state, "player", "Refuerzas las defensas y elevas la moral de la tropa.")
    elif action_type == "regroup":
        recovered = 1 if state["player"]["units"] < 6 else 0
        state["player"]["units"] = _clamp(state["player"]["units"] + recovered, minimum=0, maximum=6)
        state["player"]["morale"] = _clamp(
            state["player"]["morale"] + 2,
            minimum=0,
            maximum=12,
        )
        _append_log(
            state,
            "player",
            "Reorganizas a tus pelotones para preparar el siguiente asalto.",
        )
    else:  # recon
        state["player"]["victory_points"] += 1
        _append_log(state, "player", "Lanzas un reconocimiento para detectar flancos débiles.")

    state["turn"] = "ai"
    state.setdefault("pending_effects", {})["defence_bonus"] = defence_bonus
    _maybe_end_match(state)
    return state


def _ai_choose_action(state: Dict[str, Any]) -> str:
    if state["ai"]["units"] <= 2:
        return "regroup"
    if state["player"]["units"] <= 2:
        return "attack"
    if state["player"]["victory_points"] > state["ai"]["victory_points"]:
        return "attack"
    return random.choice(["attack", "defend", "recon"])


def apply_ai_turn(state: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve the AI opponent turn and update the match state."""

    if state.get("turn") != "ai":
        return state

    pending = state.get("pending_effects", {})
    defence_bonus = int(pending.get("defence_bonus", 0))

    action = _ai_choose_action(state)
    intensity = random.randint(1, 4)

    if action == "attack":
        damage, narrative = _resolve_damage(intensity, defence_bonus)
        state["player"]["units"] = max(0, state["player"]["units"] - damage)
        state["ai"]["victory_points"] += damage
        _append_log(
            state,
            "ai",
            f"El oponente contraataca con intensidad {intensity}. {narrative}",
        )
    elif action == "defend":
        state["ai"]["morale"] = _clamp(state["ai"]["morale"] + 1, minimum=0, maximum=12)
        _append_log(state, "ai", "El enemigo refuerza sus posiciones defensivas.")
    elif action == "regroup":
        state["ai"]["units"] = _clamp(state["ai"]["units"] + 1, minimum=0, maximum=6)
        _append_log(state, "ai", "Las reservas enemigas se incorporan al frente.")
    else:
        state["ai"]["victory_points"] += 1
        _append_log(state, "ai", "El enemigo reconoce tus líneas buscando vulnerabilidades.")

    state["turn"] = "player"
    state.pop("pending_effects", None)
    _maybe_end_match(state)
    if state.get("turn") == "player":
        _advance_round(state)
    return state


def summarise_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact summary intended for API responses."""

    return {
        "round": state.get("round", 1),
        "turn": state.get("turn", "player"),
        "player": dict(state.get("player", {})),
        "ai": dict(state.get("ai", {})),
        "log": list(state.get("log", [])),
    }


def voice_command_to_action(transcript: str) -> Dict[str, Any]:
    """Naively map a voice transcript to one of the known actions."""

    lowered = transcript.lower()
    keywords: Iterable[Tuple[str, str]] = (
        ("ata", "attack"),
        ("atac", "attack"),
        ("def", "defend"),
        ("regru", "regroup"),
        ("reor", "regroup"),
        ("recon", "recon"),
        ("explor", "recon"),
    )
    for key, action in keywords:
        if key in lowered:
            return {"type": action}
    return {"type": "recon"}

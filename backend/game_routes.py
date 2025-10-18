"""Blueprint implementing the advanced match management endpoints."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict, Tuple

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from backend.game_engine import (
    GameRuleError,
    apply_ai_turn,
    apply_player_action,
    initial_state,
    summarise_state,
    voice_command_to_action,
)
from backend.models import (
    InvitationStatus,
    Match,
    MatchEvent,
    MatchParticipant,
    MatchStatus,
    MatchInvitation,
    User,
    db,
)


game_bp = Blueprint("game", __name__)


def _current_user() -> User | None:
    user_id = get_jwt_identity()
    if not user_id:
        return None
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return None
    return db.session.get(User, user_id_int)


def _match_for_user(match_id: int, user: User) -> Match | None:
    match = db.session.get(Match, match_id)
    if not match:
        return None
    if match.host_id == user.id:
        return match
    if any(part.user_id == user.id for part in match.participants):
        return match
    if any(inv.invitee_id == user.id for inv in match.invitations):
        return match
    return None


def _serialise_match(match: Match) -> Dict[str, Any]:
    data = match.to_dict()
    data["events"] = [event.to_dict() for event in match.events]
    data["invitations"] = [inv.to_dict() for inv in match.invitations]
    return data


def _ensure_participant(match: Match, user: User, role: str = "player") -> None:
    existing = MatchParticipant.query.filter_by(match_id=match.id, user_id=user.id).first()
    if existing:
        return
    participant = MatchParticipant(match_id=match.id, user_id=user.id, role=role)
    db.session.add(participant)


@game_bp.route("/matches", methods=["GET"])
@jwt_required()
def list_matches():
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado."}), HTTPStatus.UNAUTHORIZED

    match_ids = set(part.match_id for part in user.matches)
    match_ids.update(match.id for match in user.matches_hosted)
    match_ids.update(inv.match_id for inv in user.invitations)

    matches = (
        Match.query.filter(Match.id.in_(match_ids)).all()
        if match_ids
        else []
    )

    return jsonify({"matches": [_serialise_match(match) for match in matches]})


@game_bp.route("/matches", methods=["POST"])
@jwt_required()
def create_match():
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado."}), HTTPStatus.UNAUTHORIZED

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    opponent_type = (payload.get("opponent_type") or "ai").lower()
    scenario = (payload.get("scenario") or "").strip() or None

    if not name:
        return jsonify({"error": "El nombre de la partida es obligatorio."}), HTTPStatus.BAD_REQUEST

    if opponent_type not in {"ai", "human"}:
        return jsonify({"error": "Tipo de oponente inválido."}), HTTPStatus.BAD_REQUEST

    match = Match(
        name=name,
        scenario=scenario,
        host_id=user.id,
        opponent_type=opponent_type,
        status=MatchStatus.ACTIVE if opponent_type == "ai" else MatchStatus.PENDING,
        current_turn="player",
        state=initial_state(scenario),
    )
    db.session.add(match)
    db.session.flush()

    _ensure_participant(match, user, role="host")

    if opponent_type == "ai":
        event = MatchEvent(
            match_id=match.id,
            actor="system",
            description="Se inicia un enfrentamiento contra la IA.",
        )
        db.session.add(event)
    else:
        invitee_username = (payload.get("invitee_username") or "").strip()
        if not invitee_username:
            db.session.rollback()
            return jsonify({"error": "Debes indicar un usuario a invitar."}), HTTPStatus.BAD_REQUEST

        invitee = User.query.filter_by(username=invitee_username).first()
        if not invitee:
            db.session.rollback()
            return jsonify({"error": "El usuario indicado no existe."}), HTTPStatus.NOT_FOUND

        invitation = MatchInvitation(
            match_id=match.id,
            inviter_id=user.id,
            invitee_id=invitee.id,
        )
        db.session.add(invitation)

    db.session.commit()

    return (
        jsonify({"match": _serialise_match(match)}),
        HTTPStatus.CREATED,
    )


@game_bp.route("/matches/<int:match_id>", methods=["GET"])
@jwt_required()
def retrieve_match(match_id: int):
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado."}), HTTPStatus.UNAUTHORIZED

    match = _match_for_user(match_id, user)
    if not match:
        return jsonify({"error": "No tienes acceso a esta partida."}), HTTPStatus.NOT_FOUND

    return jsonify({"match": _serialise_match(match)})


@game_bp.route("/matches/<int:match_id>/invite", methods=["POST"])
@jwt_required()
def invite_player(match_id: int):
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado."}), HTTPStatus.UNAUTHORIZED

    match = db.session.get(Match, match_id)
    if not match or match.host_id != user.id:
        return jsonify({"error": "Solo el organizador puede enviar invitaciones."}), HTTPStatus.FORBIDDEN

    if match.opponent_type != "human":
        return jsonify({"error": "Esta partida ya está configurada contra la IA."}), HTTPStatus.BAD_REQUEST

    payload = request.get_json(silent=True) or {}
    invitee_username = (payload.get("invitee_username") or "").strip()
    if not invitee_username:
        return jsonify({"error": "Debes indicar un usuario a invitar."}), HTTPStatus.BAD_REQUEST

    invitee = User.query.filter_by(username=invitee_username).first()
    if not invitee:
        return jsonify({"error": "El usuario indicado no existe."}), HTTPStatus.NOT_FOUND

    if any(part.user_id == invitee.id for part in match.participants):
        return jsonify({"error": "El usuario ya participa en la partida."}), HTTPStatus.CONFLICT

    invitation = MatchInvitation(
        match_id=match.id,
        inviter_id=user.id,
        invitee_id=invitee.id,
    )
    db.session.add(invitation)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya existe una invitación pendiente para ese usuario."}), HTTPStatus.CONFLICT

    return jsonify({"invitation": invitation.to_dict()})


@game_bp.route("/matches/<int:match_id>/accept", methods=["POST"])
@jwt_required()
def accept_invitation(match_id: int):
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado."}), HTTPStatus.UNAUTHORIZED

    invitation = MatchInvitation.query.filter_by(
        match_id=match_id, invitee_id=user.id, status=InvitationStatus.PENDING
    ).first()
    if not invitation:
        return jsonify({"error": "No hay invitaciones pendientes."}), HTTPStatus.NOT_FOUND

    match = invitation.match
    invitation.status = InvitationStatus.ACCEPTED
    _ensure_participant(match, user, role="opponent")

    if match.status == MatchStatus.PENDING:
        match.status = MatchStatus.ACTIVE
        match.current_turn = "player"
        event = MatchEvent(
            match_id=match.id,
            actor="system",
            description=f"{user.username} se une a la partida.",
        )
        db.session.add(event)

    db.session.commit()

    return jsonify({"match": _serialise_match(match)})


def _apply_player_sequence(match: Match, user: User, payload: Dict[str, Any]) -> Tuple[Match, Dict[str, Any]]:
    action = payload.get("action") or {}
    if payload.get("transcript"):
        action = voice_command_to_action(str(payload["transcript"]))
    try:
        state = apply_player_action(dict(match.state or {}), action)
    except GameRuleError as exc:
        raise GameRuleError(exc.message) from exc

    apply_ai_turn(state)

    match.state = state
    match.current_turn = state.get("turn", "completed")

    event = MatchEvent(
        match_id=match.id,
        actor=user.username,
        description=f"Acción ejecutada: {action.get('type', 'desconocida').title()}",
        payload={"action": action},
    )
    db.session.add(event)

    last_log = state.get("log", [])[-1] if state.get("log") else None
    if last_log and last_log.get("actor") == "ai":
        db.session.add(
            MatchEvent(
                match_id=match.id,
                actor="ia",
                description=last_log.get("text", ""),
            )
        )

    if state.get("turn") == "completed":
        match.status = MatchStatus.COMPLETED
        db.session.add(
            MatchEvent(
                match_id=match.id,
                actor="system",
                description="La partida ha finalizado.",
            )
        )

    db.session.commit()
    db.session.refresh(match)
    return match, summarise_state(state)


@game_bp.route("/matches/<int:match_id>/actions", methods=["POST"])
@jwt_required()
def submit_action(match_id: int):
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuario no autenticado."}), HTTPStatus.UNAUTHORIZED

    match = _match_for_user(match_id, user)
    if not match:
        return jsonify({"error": "No tienes acceso a esta partida."}), HTTPStatus.NOT_FOUND

    if match.status != MatchStatus.ACTIVE:
        return jsonify({"error": "La partida no está activa."}), HTTPStatus.BAD_REQUEST

    if match.current_turn != "player":
        return jsonify({"error": "Aún no es tu turno."}), HTTPStatus.CONFLICT

    payload = request.get_json(silent=True) or {}

    try:
        match, state = _apply_player_sequence(match, user, payload)
    except GameRuleError as exc:
        return jsonify({"error": exc.message}), HTTPStatus.BAD_REQUEST

    response: Dict[str, Any] = {
        "match": _serialise_match(match),
        "state": state,
    }
    return jsonify(response)

from __future__ import annotations

import enum
import re
from datetime import datetime, timedelta
from typing import Any, Dict

from flask_jwt_extended import create_access_token, create_refresh_token

from backend.extensions import bcrypt, db


class PasswordValidationError(ValueError):
    """Raised when a password does not meet the strength requirements."""


class MatchStatus(enum.Enum):
    """Enumerates the lifecycle states of a match."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class InvitationStatus(enum.Enum):
    """Tracks the lifecycle of an invitation sent to another player."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


def _validate_password(password: str) -> None:
    """Ensure that the provided password satisfies the security policy."""
    if password is None:
        raise PasswordValidationError("Password is required.")

    if len(password) < 8:
        raise PasswordValidationError("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        raise PasswordValidationError("Password must include at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise PasswordValidationError("Password must include at least one lowercase letter.")

    if not re.search(r"\d", password):
        raise PasswordValidationError("Password must include at least one number.")

    if not re.search(r"[^A-Za-z0-9]", password):
        raise PasswordValidationError("Password must include at least one special character.")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(128), nullable=False)
    last_password_change = db.Column(db.DateTime, nullable=True)
    matches = db.relationship(
        "MatchParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    matches_hosted = db.relationship(
        "Match",
        back_populates="host",
        cascade="all, delete-orphan",
    )
    invitations = db.relationship(
        "MatchInvitation",
        back_populates="invitee",
        cascade="all, delete-orphan",
        foreign_keys="MatchInvitation.invitee_id",
    )
    sent_invitations = db.relationship(
        "MatchInvitation",
        back_populates="inviter",
        cascade="all, delete-orphan",
        foreign_keys="MatchInvitation.inviter_id",
    )

    def set_password(self, password: str) -> None:
        _validate_password(password)
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.last_password_change = datetime.utcnow()

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    def get_token(self, expires_in: int = 3600) -> str:
        expires_delta = timedelta(seconds=max(1, int(expires_in)))
        return create_access_token(identity=str(self.id), expires_delta=expires_delta)

    def get_refresh_token(self, expires_in: int | None = None) -> str:
        expires_delta = None
        if expires_in is not None:
            expires_delta = timedelta(seconds=max(1, int(expires_in)))
        return create_refresh_token(identity=str(self.id), expires_delta=expires_delta)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "last_password_change": self.last_password_change.isoformat()
            if self.last_password_change
            else None,
        }


class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), index=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class BattleLog(db.Model):
    __tablename__ = "battle_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    scenario = db.Column(db.String(120), nullable=True)
    entries = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("battle_logs", lazy=True))


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    scenario = db.Column(db.String(120), nullable=True)
    host_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    opponent_type = db.Column(db.String(20), nullable=False, default="ai")
    status = db.Column(db.Enum(MatchStatus), nullable=False, default=MatchStatus.PENDING)
    current_turn = db.Column(db.String(20), nullable=False, default="player")
    state = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    host = db.relationship("User", back_populates="matches_hosted")
    participants = db.relationship(
        "MatchParticipant",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchParticipant.id",
    )
    events = db.relationship(
        "MatchEvent",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchEvent.created_at",
    )
    invitations = db.relationship(
        "MatchInvitation",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchInvitation.created_at",
    )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "scenario": self.scenario,
            "opponent_type": self.opponent_type,
            "status": self.status.value if isinstance(self.status, MatchStatus) else self.status,
            "current_turn": self.current_turn,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "host": self.host.to_dict() if self.host else None,
            "participants": [participant.to_dict() for participant in self.participants],
        }
        return data


class MatchParticipant(db.Model):
    __tablename__ = "match_participants"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="player")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    match = db.relationship("Match", back_populates="participants")
    user = db.relationship("User", back_populates="matches")

    __table_args__ = (
        db.UniqueConstraint("match_id", "user_id", name="uq_match_participant"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "user": self.user.to_dict() if self.user else None,
        }


class MatchEvent(db.Model):
    __tablename__ = "match_events"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    actor = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    match = db.relationship("Match", back_populates="events")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "actor": self.actor,
            "description": self.description,
            "payload": self.payload or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MatchInvitation(db.Model):
    __tablename__ = "match_invitations"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.Enum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    match = db.relationship("Match", back_populates="invitations")
    inviter = db.relationship("User", back_populates="sent_invitations", foreign_keys=[inviter_id])
    invitee = db.relationship("User", back_populates="invitations", foreign_keys=[invitee_id])

    __table_args__ = (
        db.UniqueConstraint("match_id", "invitee_id", "status", name="uq_match_invitation_status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value if isinstance(self.status, InvitationStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "invitee": self.invitee.to_dict() if self.invitee else None,
            "inviter": self.inviter.to_dict() if self.inviter else None,
        }

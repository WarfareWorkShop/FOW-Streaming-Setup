from __future__ import annotations

import enum
import re
from datetime import datetime, timedelta
from typing import Any, Dict

from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
bcrypt = Bcrypt()


class PasswordValidationError(ValueError):
    """Raised when a password does not meet the strength requirements."""


class MatchStatus(enum.Enum):
    """Enumerates the lifecycle states of a match."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


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
    role = db.Column(db.String(20), nullable=False, default="player")

    matches = db.relationship(
        "MatchParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    invitations = db.relationship(
        "MatchInvitation",
        back_populates="invitee",
        cascade="all, delete-orphan",
        foreign_keys="MatchInvitation.invitee_id",
    )

    def set_password(self, password: str) -> None:
        _validate_password(password)
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    def get_token(self, expires_in: int = 3600) -> str:
        expires_delta = timedelta(seconds=max(1, int(expires_in)))
        return create_access_token(identity=str(self.id), expires_delta=expires_delta)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
        }


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    scenario = db.Column(db.String(120), nullable=True)
    host_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    opponent_type = db.Column(db.String(20), nullable=False, default="ai")
    status = db.Column(db.Enum(MatchStatus), nullable=False, default=MatchStatus.PENDING)
    current_turn = db.Column(db.String(20), nullable=False, default="player")
    state = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    host = db.relationship("User", backref="matches_hosted", foreign_keys=[host_id])
    participants = db.relationship(
        "MatchParticipant",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    invitations = db.relationship(
        "MatchInvitation",
        back_populates="match",
        cascade="all, delete-orphan",
    )
    events = db.relationship(
        "MatchEvent",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="MatchEvent.created_at",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "scenario": self.scenario,
            "status": self.status.value,
            "opponent_type": self.opponent_type,
            "current_turn": self.current_turn,
            "state": self.state or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "participants": [p.to_dict() for p in self.participants],
        }


class MatchParticipant(db.Model):
    __table_args__ = (db.UniqueConstraint("match_id", "user_id", name="uq_match_user"),)

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="player")

    match = db.relationship("Match", back_populates="participants")
    user = db.relationship("User", back_populates="matches")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "role": self.role,
            "user": self.user.to_dict() if self.user else None,
        }


class InvitationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class MatchInvitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(
        db.Enum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    match = db.relationship("Match", back_populates="invitations")
    inviter = db.relationship(
        "User", foreign_keys=[inviter_id], backref="sent_invitations"
    )
    invitee = db.relationship("User", foreign_keys=[invitee_id], back_populates="invitations")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "status": self.status.value,
            "invitee": self.invitee.to_dict() if self.invitee else None,
            "created_at": self.created_at.isoformat(),
        }


class MatchEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    actor = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text, nullable=False)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    match = db.relationship("Match", back_populates="events")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "actor": self.actor,
            "description": self.description,
            "payload": self.payload or {},
            "created_at": self.created_at.isoformat(),
        }

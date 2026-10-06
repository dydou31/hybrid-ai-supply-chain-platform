from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class CloudPasskey(Base):
    __tablename__ = "cloud_passkeys"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    credential_id = Column(Text, nullable=False, unique=True)
    credential_public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, nullable=False, default=0)


class CloudWebAuthnChallenge(Base):
    __tablename__ = "cloud_webauthn_challenges"

    id = Column(String, primary_key=True)
    challenge = Column(Text, nullable=False)
    purpose = Column(String, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

"""SQLAlchemy models for the 18 tables in docs/sql/001_init.sql.

These reflect that file. They do not own it and they do not create anything:
run the SQL, then let the models match. Enums are declared with the exact values
from contracts/ENUMS.md — a typo here is a bug in two layers.
"""
from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# pgvector is optional: without it the column type falls back to an opaque text
# column, which is enough for everything except similarity search.
try:  # pragma: no cover - depends on the environment
    from pgvector.sqlalchemy import Vector  # type: ignore

    EMBEDDING = Vector(384)
except Exception:  # noqa: BLE001
    EMBEDDING = Text()


class Base(DeclarativeBase):
    pass


def _enum(name: str, values: list[str]):
    return Enum(*values, name=name, schema="public", create_type=False)


SkillStatus = _enum(
    "skill_status",
    ["claimed", "unverified", "weak", "developing", "verified", "needs_revision"],
)
ProficiencyLevel = _enum(
    "proficiency_level",
    ["none", "listed", "beginner", "intermediate", "advanced", "expert"],
)
VerifiedLevel = _enum(
    "verified_level", ["none", "beginner", "intermediate", "advanced", "expert"]
)
PriorityBand = _enum("priority_band", ["critical", "high", "medium", "low"])
EvidenceType = _enum(
    "evidence_type",
    [
        "resume_skill_list",
        "resume_project",
        "resume_experience",
        "assessment_answer",
        "interview_answer",
        "user_correction",
    ],
)
AssessmentLevel = _enum("assessment_level", ["conceptual", "practical", "applied"])
AssessmentStatus = _enum("assessment_status", ["in_progress", "completed"])
QuestionType = _enum(
    "question_type",
    [
        "fundamentals",
        "advanced",
        "coding",
        "debugging",
        "project_deep_dive",
        "scenario",
        "system_design",
        "behavioral",
    ],
)
InterviewMode = _enum(
    "interview_mode",
    [
        "beginner_practice",
        "intermediate_technical",
        "advanced_technical",
        "resume_based",
        "jd_based",
        "full_mock",
    ],
)
Channel = _enum("channel", ["text", "voice"])
SessionStatus = _enum("session_status", ["active", "completed"])
MessageRole = _enum("message_role", ["interviewer", "candidate", "system"])
ResourceRole = _enum("resource_role", ["concept", "practice", "checkpoint"])
ResourceKind = _enum(
    "resource_kind",
    ["docs", "article", "video", "course", "exercise", "repo", "paper", "book"],
)
ParseStatus = _enum("parse_status", ["ok", "degraded"])
ReadinessLabel = _enum(
    "readiness_label", ["not_ready", "early", "approaching", "interview_ready"]
)
TopicStatus = _enum(
    "topic_status", ["not_started", "in_progress", "checkpoint_passed", "done"]
)
TopicDepth = _enum("topic_depth", ["refresh", "core", "deep_dive"])
PathStatus = _enum("path_status", ["active", "completed"])
Seniority = _enum("seniority", ["intern", "junior", "mid", "senior", "lead"])
JobStatus = _enum("job_status", ["queued", "running", "done", "failed"])


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str | None] = mapped_column(Text)
    full_name: Mapped[str | None] = mapped_column(Text)
    target_role: Mapped[str | None] = mapped_column(Text)
    target_company: Mapped[str | None] = mapped_column(Text)
    seniority: Mapped[str | None] = mapped_column(Seniority)
    interview_date: Mapped[dt.date | None] = mapped_column(Date)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    filename: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    storage_path: Mapped[str | None] = mapped_column(Text)
    raw_text: Mapped[str | None] = mapped_column(Text)
    parse_status: Mapped[str] = mapped_column(ParseStatus, default="ok")
    parse_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    skills: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    projects: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    experience_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    achievements: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    unsupported_claims: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(Text)
    company: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(Text)
    seniority: Mapped[str | None] = mapped_column(Seniority)
    min_years_experience: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    body: Mapped[str] = mapped_column(Text)
    parse_status: Mapped[str] = mapped_column(ParseStatus, default="ok")
    requirements: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    interview_rounds: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    rounds_inferred: Mapped[bool] = mapped_column(Boolean, default=True)
    topics: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    interview_relevance: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.5"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SkillSubtopic(Base):
    __tablename__ = "skill_subtopics"
    skill_id: Mapped[str] = mapped_column(Text, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    subtopic_id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(ProficiencyLevel, default="beginner")
    objective: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    embedding: Mapped[Any | None] = mapped_column(EMBEDDING)


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="candidate_skills_user_id_skill_id_key"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    skill_id: Mapped[str] = mapped_column(Text, ForeignKey("skills.id"))
    status: Mapped[str] = mapped_column(SkillStatus, default="claimed")
    claimed_level: Mapped[str | None] = mapped_column(ProficiencyLevel)
    verified_level: Mapped[str | None] = mapped_column(VerifiedLevel)
    expected_level: Mapped[str | None] = mapped_column(VerifiedLevel)
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    jd_importance: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    interview_relevance: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.5"))
    gap: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    priority: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0)
    priority_band: Mapped[str] = mapped_column(PriorityBand, default="low")
    explanation: Mapped[str] = mapped_column(Text)
    in_resume: Mapped[bool] = mapped_column(Boolean, default=False)
    in_jd: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    last_assessed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    skill_id: Mapped[str] = mapped_column(Text, ForeignKey("skills.id"))
    level: Mapped[str] = mapped_column(AssessmentLevel, default="conceptual")
    status: Mapped[str] = mapped_column(AssessmentStatus, default="in_progress")
    question_index: Mapped[int] = mapped_column(Integer, default=1)
    question_total: Mapped[int] = mapped_column(Integer, default=3)
    plan: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    inferred_level: Mapped[str | None] = mapped_column(VerifiedLevel)
    status_after: Mapped[str | None] = mapped_column(SkillStatus)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"
    __table_args__ = (
        UniqueConstraint("assessment_id", "question_index", name="assessment_answers_assessment_id_question_index_key"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    question_index: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(QuestionType)
    answer_text: Mapped[str] = mapped_column(Text, default="")
    scores: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    missing_concepts: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    feedback: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text, default="Your preparation path")
    summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(PathStatus, default="active")
    target_role: Mapped[str | None] = mapped_column(Text)
    readiness: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    readiness_label: Mapped[str] = mapped_column(ReadinessLabel, default="not_ready")
    generated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningTopic(Base):
    __tablename__ = "learning_topics"
    __table_args__ = (UniqueConstraint("path_id", "order_index", name="learning_topics_path_id_order_index_key"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    skill_id: Mapped[str | None] = mapped_column(Text, ForeignKey("skills.id"))
    title: Mapped[str] = mapped_column(Text)
    objective: Mapped[str | None] = mapped_column(Text)
    subtopics: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    depth: Mapped[str] = mapped_column(TopicDepth, default="core")
    status: Mapped[str] = mapped_column(TopicStatus, default="not_started")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)
    progress: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Resource(Base):
    __tablename__ = "resources"
    # Composite FK to skill_subtopics: which subtopic a tier-0 row answers for.
    __table_args__ = (
        ForeignKeyConstraint(
            ["curated_skill_id", "curated_subtopic_id"],
            ["skill_subtopics.skill_id", "skill_subtopics.subtopic_id"],
            ondelete="SET NULL",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str | None] = mapped_column(ResourceKind)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    license: Mapped[str | None] = mapped_column(Text)
    tier: Mapped[int] = mapped_column(SmallInteger, default=6)
    curated_skill_id: Mapped[str | None] = mapped_column(Text)
    curated_subtopic_id: Mapped[str | None] = mapped_column(Text)
    embedding: Mapped[Any | None] = mapped_column(EMBEDDING)
    http_status: Mapped[int | None] = mapped_column(Integer)
    is_dead: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TopicResource(Base):
    __tablename__ = "topic_resources"
    __table_args__ = (
        UniqueConstraint("topic_id", "role", "resource_id", name="topic_resources_topic_id_role_resource_id_key"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_topics.id", ondelete="CASCADE"))
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(ResourceRole)
    score: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0)
    why: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResourceCheck(Base):
    __tablename__ = "resource_checks"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"))
    checked_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    http_status: Mapped[int | None] = mapped_column(Integer)
    final_url: Mapped[str | None] = mapped_column(Text)
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(Text)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    mode: Mapped[str] = mapped_column(InterviewMode, default="jd_based")
    channel: Mapped[str] = mapped_column(Channel, default="text")
    status: Mapped[str] = mapped_column(SessionStatus, default="active")
    target_role: Mapped[str | None] = mapped_column(Text)
    skill_focus: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    asked: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=6)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class InterviewMessage(Base):
    __tablename__ = "interview_messages"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(MessageRole)
    content: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str | None] = mapped_column(QuestionType)
    skill_id: Mapped[str | None] = mapped_column(Text, ForeignKey("skills.id"))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewReport(Base):
    __tablename__ = "interview_reports"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    overall_scores: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    per_skill: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    strengths: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    gaps: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    weak_answers: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    next_actions: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LLMCache(Base):
    __tablename__ = "llm_cache"
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    model: Mapped[str] = mapped_column(Text)
    schema_version: Mapped[int] = mapped_column(Integer, default=1)
    prompt_snippet: Mapped[str | None] = mapped_column(Text)
    response: Mapped[dict[str, Any]] = mapped_column(JSONB)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    hits: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(JobStatus, default="queued")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    run_after: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


ALL_MODELS = [
    Profile, Resume, JobDescription, Skill, SkillSubtopic, CandidateSkill,
    Assessment, AssessmentAnswer, LearningPath, LearningTopic, Resource,
    TopicResource, ResourceCheck, InterviewSession, InterviewMessage,
    InterviewReport, LLMCache, Job,
]

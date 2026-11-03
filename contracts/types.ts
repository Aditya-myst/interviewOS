/**
 * Hand-maintained mirror of contracts/openapi.yaml (0.1.0).
 * Once the backend boots, regenerate with:
 *   npx openapi-typescript ../contracts/openapi.yaml -o types/api.ts
 * Until then, the UI imports THESE types. Never invent fields.
 */

export type SkillStatus =
  | "claimed" | "unverified" | "weak" | "developing" | "verified" | "needs_revision";

export type Level = "none" | "listed" | "beginner" | "intermediate" | "advanced" | "expert";
export type VerifiedLevel = "none" | "beginner" | "intermediate" | "advanced" | "expert";
export type PriorityBand = "critical" | "high" | "medium" | "low";
export type RequirementType = "required" | "preferred";
export type EvidenceType =
  | "resume_skill_list" | "resume_project" | "resume_experience" | "resume_summary"
  | "jd_requirement"
  | "assessment_answer" | "interview_answer" | "user_correction";
export type AssessmentLevel = "conceptual" | "practical" | "applied";
export type QuestionType =
  | "fundamentals" | "advanced" | "coding" | "debugging"
  | "project_deep_dive" | "scenario" | "system_design" | "behavioral";
export type InterviewMode =
  | "beginner_practice" | "intermediate_technical" | "advanced_technical"
  | "resume_based" | "jd_based" | "full_mock";
export type Channel = "text" | "voice";
export type ResourceRole = "concept" | "practice" | "checkpoint";
export type ParseStatus = "ok" | "degraded";
export type ReadinessLabel = "not_ready" | "early" | "approaching" | "interview_ready";
export type TopicStatus = "not_started" | "in_progress" | "checkpoint_passed" | "done";

export type ErrorCode =
  | "not_found" | "bad_input" | "unauthenticated" | "invalid_token"
  | "unsupported_file" | "file_too_large" | "parse_failed" | "llm_unavailable"
  | "quota_exceeded" | "degraded_mode" | "insufficient_evidence";

export interface ErrorEnvelope {
  error: { code: ErrorCode | string; message: string; detail?: string | null };
}

export interface Profile {
  id: string;
  email?: string | null;
  full_name?: string | null;
  target_role?: string | null;
  target_company?: string | null;
  seniority?: "intern" | "junior" | "mid" | "senior" | "lead" | null;
  interview_date?: string | null;
  created_at: string;
}

export interface ProfileUpdate {
  full_name?: string;
  target_role?: string;
  target_company?: string;
  seniority?: "intern" | "junior" | "mid" | "senior" | "lead";
  interview_date?: string | null;
}

export interface Evidence {
  type: EvidenceType;
  quote: string;
  section?: string | null;
  start?: number | null;
  end?: number | null;
  source_id?: string | null;
  created_at?: string;
}

export interface ExtractedSkill {
  skill_id: string;
  name: string;
  category?: string | null;
  claimed_level: Level;
  confidence: number;
  in_resume: boolean;
  evidence: Evidence[];
}

export interface ParsedProject {
  title: string;
  description?: string;
  technologies?: string[];
  highlights?: string[];
}

export interface ParsedResume {
  id: string;
  filename?: string | null;
  parse_status: ParseStatus;
  parse_meta?: {
    model?: string;
    prompt_hash?: string;
    parse_version?: number;
    extracted_chars?: number;
    warn?: string | null;
  };
  skills: ExtractedSkill[];
  projects: ParsedProject[];
  experience_years?: number | null;
  achievements?: string[];
  unsupported_claims?: string[];
  created_at?: string;
}

export interface JDInput { title?: string | null; company?: string | null; text: string }

export interface JDRequirement {
  skill_id: string;
  name: string;
  requirement_type: RequirementType;
  jd_importance: number;
  expected_level: VerifiedLevel;
  mentions?: number;
  evidence?: Evidence[];
}

export interface ParsedJD {
  id: string;
  title?: string | null;
  company?: string | null;
  role: string;
  seniority?: string | null;
  min_years_experience?: number | null;
  requirements: JDRequirement[];
  interview_rounds: Array<
    | "technical" | "coding" | "system_design" | "take_home" | "behavioral" | "hr"
    | "portfolio_review" | "content_task" | "analytics_case"
  >;
  rounds_inferred?: boolean;
  topics?: string[];
  parse_status: ParseStatus;
  created_at?: string;
}

export interface CandidateSkill {
  skill_id: string;
  name: string;
  category?: string | null;
  status: SkillStatus;
  claimed_level?: Level | null;
  verified_level?: VerifiedLevel | null;
  expected_level?: VerifiedLevel | null;
  confidence: number;
  jd_importance: number;
  interview_relevance: number;
  gap: number;
  priority: number;
  priority_band: PriorityBand;
  /** server-generated sentence; render verbatim, never recompute */
  explanation: string;
  in_resume: boolean;
  in_jd: boolean;
  evidence: Evidence[];
  last_assessed_at?: string | null;
}

export interface CoverageRow { category: string; verified: number; developing: number; unverified: number }

export interface SkillProfile {
  skills: CandidateSkill[];
  counts: {
    critical: number; high: number; medium: number; low: number;
    verified: number; unverified: number;
  };
  provisional: boolean;
  coverage_by_category?: CoverageRow[];
}

export interface SkillCorrection {
  skill_id: string;
  action: "remove" | "set_claimed_level" | "add";
  claimed_level?: "listed" | "beginner" | "intermediate" | "advanced" | "expert";
}

export interface Resource {
  id: string;
  role: ResourceRole;
  title: string;
  url: string;
  provider: string;
  author?: string | null;
  kind?: "docs" | "article" | "video" | "course" | "exercise" | "repo" | "paper" | "book" | null;
  duration_minutes?: number | null;
  is_paid: boolean;
  license?: string | null;
  verified_at?: string | null;
  why?: string;
}

export interface LearningTopic {
  id: string;
  skill_id?: string | null;
  skill_name?: string | null;
  title: string;
  objective?: string | null;
  status: TopicStatus;
  depth: "refresh" | "core" | "deep_dive";
  order_index: number;
  estimated_minutes?: number | null;
  subtopics?: string[];
  progress: number;
  resources: Resource[];
  /**
   * Roles the catalogue cannot fill for this topic. The API populates this rather
   * than leaving an empty slot: an unfilled checkpoint is a fact about the
   * catalogue, and the screen is required to say so.
   */
  missing_roles?: Array<"concept" | "practice" | "checkpoint">;
}

export interface Roadmap {
  id: string;
  summary: string;
  status: "active" | "completed";
  target_role?: string | null;
  topics: LearningTopic[];
  progress?: { done: number; total: number };
}

export interface PreparationPlan {
  id: string;
  readiness: number;
  readiness_label: ReadinessLabel;
  skill_profile: SkillProfile;
  roadmap: Roadmap;
  next_best_action: string;
  generated_at: string;
  parse_status: ParseStatus;
}

export interface RubricScores {
  technical_correctness?: number;
  depth?: number;
  practical_ability?: number;
  problem_solving?: number;
  communication?: number;
}

export interface AssessmentState {
  assessment_id: string;
  skill_id: string;
  skill_name?: string;
  level: AssessmentLevel;
  status: "in_progress" | "completed";
  question_index?: number;
  question_total?: number;
  question?: { text: string; question_type: QuestionType; hint?: string | null } | null;
  feedback?: { scores: RubricScores; missing_concepts: string[]; summary: string } | null;
  result?: {
    inferred_level: VerifiedLevel;
    status_after: "weak" | "developing" | "verified" | "needs_revision";
    confidence: number;
  } | null;
}

export interface TutorReply {
  reply: string;
  citations?: Resource[];
  checkpoint_ready: boolean;
  suggested_next?: string | null;
}

export interface InterviewState {
  session_id: string;
  status: "active" | "completed";
  asked: number;
  total: number;
  question?: {
    text: string; question_type: QuestionType; skill_id?: string | null;
    source: "jd" | "resume_project" | "weak_skill" | "verified_skill" | "general";
    /** Display name of the skill the question came from. */
    skill_name?: string;
    /** How many rubric points the answer is scored against. */
    rubric_size?: number;
  } | null;
}

/**
 * Per-answer scoring. `quote` is a verbatim substring of what the candidate said, or
 * null — and null means the answer earned no credit, not that the quote was omitted.
 */
export interface InterviewFeedback {
  skill_id?: string | null;
  skill_name: string;
  score: number;
  status_after: "weak" | "developing" | "verified" | "needs_revision";
  quote?: string | null;
  matched: string[];
  missing: string[];
  why: string;
  /** "rubric" today: the score came from the taxonomy rubric, not a model. */
  scored_by?: string;
  flags?: string[];
}

/** One turn of the loop: where the session stands, what the last answer earned. */
export interface InterviewAnswerResult {
  state: InterviewState;
  feedback: InterviewFeedback;
  /** Present only on the answer that closes the session. */
  report?: InterviewReport | null;
}

export interface Transcript {
  session_id: string;
  messages: Array<{
    role: "interviewer" | "candidate" | "system";
    content: string;
    question_type?: string | null;
    created_at?: string;
  }>;
}

export interface InterviewReport {
  session_id: string;
  /** false when the session lived in memory and will not survive a restart. */
  persisted?: boolean;
  scored_by?: string;
  overall_scores: {
    overall?: number; technical?: number; problem_solving?: number;
    /** transcript-derived only — the UI must label it as such */
    communication_transcript_based?: number;
  };
  per_skill: Array<{
    skill_id: string; name: string; score: number;
    status_after: "weak" | "developing" | "verified" | "needs_revision"; comment: string;
  }>;
  strengths: string[];
  gaps: string[];
  weak_answers?: Array<{ question: string; why_weak: string; better_answer_outline: string[] }>;
  next_actions: string[];
  created_at?: string;
}

export interface Dashboard {
  readiness: number;
  readiness_label: ReadinessLabel;
  provisional: boolean;
  target_role?: string | null;
  stats: {
    verified_skills: number; skills_total: number; mock_interviews: number;
    topics_done: number; topics_total: number; avg_interview_score?: number | null;
  };
  coverage: CoverageRow[];
  /** Last 14 days, oldest first. Absent means "no trend", never zero. */
  readiness_history?: Array<{ date: string; readiness: number }>;
  priority_skills: CandidateSkill[];
  interviews: Array<{
    session_id: string; mode: string; channel: string;
    score?: number | null; duration_minutes?: number | null; created_at: string;
  }>;
}

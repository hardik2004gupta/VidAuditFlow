"""Modular prompt templates for the LLM-calling agents.

AI_PIPELINE_VISION.md section 10 asks for prompts that separate static
*instructions* from per-run *context*, and that keep policy text separate
from transcript/OCR text -- rather than one giant f-string interpolating
everything together (the Phase 2 design). Each prompt here is split into:

- a static ``*_SYSTEM_PROMPT`` constant (the model's role + instructions,
  identical on every call), and
- a ``build_*_context()`` function that formats that call's data into
  clearly delimited Markdown sections.

Because both LLM-calling agents now use structured output
(``with_structured_output``), neither prompt needs to describe a JSON
schema in prose -- LangChain binds the Pydantic schema directly, so the
prompt can stay focused on the actual reasoning task.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.src.schemas.audit import ComplianceIssue, RetrievedRule

# ---------------------------------------------------------------------------
# Compliance Agent
# ---------------------------------------------------------------------------

COMPLIANCE_SYSTEM_PROMPT = """\
You are a Senior Brand Compliance Auditor reviewing video advertising content.

Your job is to compare the video's spoken transcript and on-screen text
against the official regulatory policies provided to you, and identify any
violations.

Rules for your analysis:
1. Only flag a violation if it is clearly supported by the transcript or
   on-screen text AND is plausibly covered by the provided policies.
2. For every violation, quote the exact phrase or on-screen text that
   triggered it as `evidence`.
3. For every violation, cite which policy it relates to in
   `policy_reference` when one of the provided policies clearly applies.
   If no policy was provided, or none clearly applies, leave it unset --
   do not invent a policy citation.
4. Assign a `confidence` between 0.0 and 1.0 reflecting how certain you are
   this is a genuine violation, not a borderline or ambiguous case.
5. Provide a concrete, actionable `recommendation` for how the creator could
   fix each specific violation.
6. Set `overall_status` to "FAIL" if you found at least one violation, or
   "PASS" if you found none.
7. If no policies were provided at all, you may still flag clearly unlawful
   or deceptive claims using general advertising-compliance judgment, but
   note in the description that this finding is not grounded in a specific
   provided policy.
"""


def build_compliance_context(
    transcript: str,
    ocr_text: List[str],
    retrieved_rules: List[RetrievedRule],
    video_metadata: Dict[str, Any],
) -> str:
    """Format one call's data for the Compliance Agent as clearly delimited Markdown."""
    if retrieved_rules:
        policy_section = "\n\n".join(f"[Source: {rule.source}]\n{rule.content}" for rule in retrieved_rules)
    else:
        policy_section = "(No policies were retrieved for this video. Rely on general advertising-compliance judgment only, and say so in any findings.)"

    ocr_section = "\n".join(f"- {line}" for line in ocr_text) if ocr_text else "(No on-screen text detected.)"

    return f"""\
## Video Metadata
{video_metadata or "(none available)"}

## Retrieved Policies
{policy_section}

## Transcript
{transcript}

## On-Screen Text (OCR)
{ocr_section}
"""


# ---------------------------------------------------------------------------
# Summary Agent
# ---------------------------------------------------------------------------

SUMMARY_SYSTEM_PROMPT = """\
You are a compliance analyst writing a short executive summary for a brand
manager who has 10 seconds to read it.

Given a list of already-identified compliance violations (with severity and
confidence) and an overall compliance score, write a 2-4 sentence executive
summary in plain, direct language. State the verdict, the number and
severity of violations, and the single most important thing the reader
should know. Do not repeat the raw list of violations -- that is shown
separately. Do not invent violations not present in the data you were
given.
"""


def build_summary_context(
    violations: List[ComplianceIssue],
    compliance_score: float,
    risk_level: str,
) -> str:
    """Format the structured violation data for the Summary Agent's narrative call."""
    if not violations:
        violations_section = "(No violations were found.)"
    else:
        violations_section = "\n".join(
            f"- [{v.severity}] {v.category}: {v.description} (confidence {v.confidence:.2f})"
            for v in violations
        )

    return f"""\
## Compliance Score
{compliance_score:.0f} / 100

## Risk Level
{risk_level}

## Violations
{violations_section}
"""

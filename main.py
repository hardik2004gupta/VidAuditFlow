"""
Main Execution Entry Point for Brand Guardian AI.

This file is the "control center" that starts and manages the entire
compliance audit workflow. Think of it as the master switch that:
1. Sets up the audit request
2. Runs the AI workflow
3. Displays the final compliance report
"""

import asyncio
import json
import uuid

from dotenv import load_dotenv

# Load environment variables from .env before importing anything that reads
# configuration (core.config, the graph, Azure SDKs, etc.).
load_dotenv(override=True)

from backend.src.core.logging import get_logger  # noqa: E402
from backend.src.graph.adapters import to_audit_result  # noqa: E402
from backend.src.graph.workflow import app  # noqa: E402

logger = get_logger("brand-guardian-runner")


async def run_cli_simulation() -> None:
    """
    Simulates a Video Compliance Audit request.

    This function orchestrates the entire audit process:
    - Creates a unique session ID
    - Prepares the video URL and metadata
    - Runs it through the AI workflow
    - Displays the compliance results
    """

    # ========== STEP 1: GENERATE SESSION ID ==========
    session_id = str(uuid.uuid4())
    logger.info(f"Starting Audit Session: {session_id}")

    # ========== STEP 2: DEFINE INITIAL STATE ==========
    video_id = f"vid_{session_id[:8]}"
    initial_inputs = {
        "video_url": "https://youtu.be/dT7S75eYhcQ",
        "video_id": video_id,
    }

    # ========== DISPLAY SECTION: INPUT SUMMARY ==========
    print("\n--- 1. Input Payload: INITIALIZING WORKFLOW ---")
    print(json.dumps(initial_inputs, indent=2))

    # ========== STEP 3: EXECUTE GRAPH ==========
    try:
        # Flow: START -> supervisor_start -> [transcript_agent, ocr_agent]
        #       -> supervisor_join -> retrieval_agent -> compliance_agent
        #       -> summary_agent -> END
        run_config = {
            "run_name": f"audit-{video_id}",
            "tags": ["vidauditflow", "audit", "cli"],
            "metadata": {"video_id": video_id, "session_id": session_id},
        }
        final_state = await app.ainvoke(initial_inputs, config=run_config)

        # The graph's internal state is richer than the public API contract
        # (job_status, confidence_score, risk_level, per-stage traces, ...);
        # `to_audit_result` is the single place that maps it down to the
        # same {status, final_report, compliance_results} shape the API
        # returns, so the CLI and the API always agree.
        result = to_audit_result(final_state, fallback_video_id=video_id)

        # ========== DISPLAY SECTION: EXECUTION COMPLETE ==========
        print("\n--- 2. WORKFLOW EXECUTION COMPLETE ---")
        print("\n=== COMPLIANCE AUDIT REPORT ===")
        print(f"Video ID:    {result.video_id}")
        print(f"Status:      {result.status}")

        # ========== VIOLATIONS SECTION ==========
        print("\n[ VIOLATIONS DETECTED ]")

        if result.compliance_results:
            for issue in result.compliance_results:
                print(f"- [{issue.severity}] {issue.category}: {issue.description}")
        else:
            print("No violations found.")

        # ========== SUMMARY SECTION ==========
        print("\n[ FINAL SUMMARY ]")
        print(result.final_report)

    except Exception as e:
        logger.error(f"Workflow Execution Failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(run_cli_simulation())


"""
You have moved from "Coding" to "Product."

Ingestion:  (YouTube -> Azure)

Indexing:  (Speech-to-Text + OCR)

Retrieval:  (Found the rules about "Claims")

Reasoning:  (Applied rules to the specific claims in the video)

You are done. Your pipeline is fully operational.
"""

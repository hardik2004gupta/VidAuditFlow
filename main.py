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
    initial_inputs = {
        "video_url": "https://youtu.be/dT7S75eYhcQ",
        "video_id": f"vid_{session_id[:8]}",
        "compliance_results": [],
        "errors": [],
    }

    # ========== DISPLAY SECTION: INPUT SUMMARY ==========
    print("\n--- 1. Input Payload: INITIALIZING WORKFLOW ---")
    print(json.dumps(initial_inputs, indent=2))

    # ========== STEP 3: EXECUTE GRAPH ==========
    try:
        # Flow: START -> Indexer -> Auditor -> END
        final_state = await app.ainvoke(initial_inputs)

        # ========== DISPLAY SECTION: EXECUTION COMPLETE ==========
        print("\n--- 2. WORKFLOW EXECUTION COMPLETE ---")
        print("\n=== COMPLIANCE AUDIT REPORT ===")
        print(f"Video ID:    {final_state.get('video_id')}")
        print(f"Status:      {final_state.get('final_status')}")

        # ========== VIOLATIONS SECTION ==========
        print("\n[ VIOLATIONS DETECTED ]")
        results = final_state.get("compliance_results", [])

        if results:
            for issue in results:
                # Each issue is a dict with: severity, category, description
                print(f"- [{issue.get('severity')}] {issue.get('category')}: {issue.get('description')}")
        else:
            print("No violations found.")

        # ========== SUMMARY SECTION ==========
        print("\n[ FINAL SUMMARY ]")
        print(final_state.get("final_report"))

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

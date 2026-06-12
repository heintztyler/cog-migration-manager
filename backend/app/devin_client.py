"""
Devin API client for creating and monitoring migration sessions.
Uses the Devin REST API to create sessions that generate migration scripts.
"""

import os
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEVIN_API_BASE = "https://api.devin.ai/v1"


class DevinClient:
    def __init__(self):
        self.api_key = os.environ.get("DEVIN_API_KEY", "")
        self.base_url = DEVIN_API_BASE
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def create_session(
        self,
        prompt: str,
        title: str,
    ) -> dict:
        """Create a new Devin session for a migration task."""
        if not self.is_configured:
            logger.warning("Devin API key not configured - returning mock session")
            return self._mock_session(title)

        client = self._get_client()
        try:
            response = await client.post(
                "/sessions",
                json={
                    "prompt": prompt,
                    "title": title,
                },
            )
            response.raise_for_status()
            data = response.json()
            return {
                "session_id": data.get("session_id", ""),
                "url": data.get("url", f"https://app.devin.ai/sessions/{data.get('session_id', '')}"),
                "status": "running",
            }
        except Exception as e:
            logger.error(f"Failed to create Devin session: {e}")
            return self._mock_session(title)

    async def get_session_status(self, session_id: str) -> dict:
        """Get the current status of a Devin session, including PR info."""
        if not self.is_configured:
            return {
                "session_id": session_id,
                "status": "running",
                "status_message": "Devin is analyzing schemas and generating migration script...",
            }

        client = self._get_client()
        try:
            response = await client.get(f"/sessions/{session_id}")
            response.raise_for_status()
            data = response.json()

            result: dict = {
                "session_id": session_id,
                "status": data.get("status_enum", data.get("status", "unknown")),
                "status_message": data.get("status_message", ""),
            }

            # Extract PR info from pull_request field (PullRequestInfo / SessionPullRequest)
            pr = data.get("pull_request")
            if pr:
                pr_url = pr.get("pr_url", pr.get("url", ""))
                if pr_url:
                    result["pr_url"] = pr_url
                    result["pr_state"] = pr.get("pr_state", pr.get("state"))
                    # Extract PR number from URL
                    try:
                        result["pr_number"] = int(pr_url.rstrip("/").split("/")[-1])
                    except (ValueError, IndexError):
                        pass

            return result
        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            return {
                "session_id": session_id,
                "status": "unknown",
                "status_message": f"Error checking status: {str(e)}",
            }

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def _mock_session(title: str) -> dict:
        import uuid
        mock_id = f"demo-{uuid.uuid4().hex[:8]}"
        return {
            "session_id": mock_id,
            "url": "",
            "status": "running",
        }


def build_migration_prompt(
    dataset_id: str,
    dataset_name: str,
    source_system: str,
    source_schema: dict,
    target_schema: dict,
    sample_data: list[dict],
    repo_url: str,
) -> str:
    """Build a detailed prompt for Devin to generate a migration script."""

    source_fields = "\n".join(
        f"  - {f['name']} ({f['type']}): {f['description']}"
        for f in source_schema["fields"]
    )
    target_fields = "\n".join(
        f"  - {f['name']} ({f['type']}): {f['description']}"
        for f in target_schema["fields"]
    )

    sample_str = ""
    for i, row in enumerate(sample_data[:3]):
        sample_str += f"\n  Record {i+1}: {row}"

    return f"""You are performing a data migration for the Army Logistics ERP Consolidation project.

## Task
Generate a Python migration script that transforms data from the legacy **{source_system}** system's `{source_schema['table_name']}` table into the new unified ALERP `{target_schema['table_name']}` table format.

## Source Schema ({source_system} - {source_schema['table_name']})
{source_schema['description']}
Fields:
{source_fields}

## Target Schema (ALERP - {target_schema['table_name']})
{target_schema['description']}
Fields:
{target_fields}

## Sample Source Data
{sample_str}

## Requirements
1. Create a Python script at `migrations/{dataset_id}_migration.py` that:
   - Reads source data (assume it's provided as a list of dicts)
   - Maps each source field to the appropriate target field
   - Handles type conversions (e.g., SAP date formats, decimal precision)
   - Generates UUIDs for new primary keys
   - Preserves legacy system ID and source system reference
   - Adds proper audit timestamps (created_at, updated_at)
   - Handles NULL/empty values gracefully
   - Includes data validation checks

2. Create a test file at `migrations/test_{dataset_id}_migration.py` that:
   - Tests the transformation with the sample data
   - Validates all required fields are populated
   - Checks type correctness of output
   - Verifies edge cases (NULL values, empty strings)

3. Include a brief README section or docstring explaining the mapping logic

## Repository
Clone the repo at {repo_url} and commit your migration scripts to the `migrations/` directory.
Create a branch named `migration/{dataset_id}` and push your changes.

## Important
- Use only Python standard library + uuid module
- Make the script idempotent (safe to re-run)
- Log transformation statistics (records processed, skipped, errors)
- Follow the existing code style in the repository
"""

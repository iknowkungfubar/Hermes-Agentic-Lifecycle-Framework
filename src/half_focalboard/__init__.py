"""
HALF — Focalboard Integration Wrapper

API client for the Focalboard Kanban board.
Focalboard is an open-source project management tool
that serves as the Swarm Overview in the Command Center.

Focalboard runs as a Docker container and exposes a REST API.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger("half.focalboard")


@dataclass
class FocalboardBoard:
    """A Focalboard board (project/workspace)."""

    id: str
    title: str
    description: str = ""
    card_count: int = 0


@dataclass
class FocalboardCard:
    """A card (task/ticket) in a Focalboard board."""

    id: str
    title: str
    description: str = ""
    status: str = "open"  # open, in-progress, done, blocked
    assignee: str = ""
    phase: str = ""
    priority: str = "medium"


class FocalboardClient:
    """REST API client for Focalboard.

    Connects to a local Focalboard instance and manages
    tickets for the HALF pipeline phases.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        api_token: str = "",
        team_id: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.team_id = team_id
        self.headers = {
            "Content-Type": "application/json",
        }
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Focalboard API.

        Args:
            method: HTTP method.
            path: API path (e.g., /api/v1/boards).
            data: Optional JSON body.

        Returns:
            JSON response as dict.

        Raises:
            RuntimeError: If the request fails.
        """
        url = f"{self.base_url}/api/v1{path}"
        body = json.dumps(data).encode("utf-8") if data else None

        req = Request(
            url,
            data=body,
            headers=self.headers,
            method=method,
        )

        try:
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except URLError as e:
            logger.warning("Focalboard API error: %s", e)
            raise RuntimeError(f"Focalboard API error: {e}")
        except json.JSONDecodeError:
            return {}

    # ─── Board Operations ────────────────────────────────────────────────

    def create_board(self, title: str, description: str = "") -> FocalboardBoard:
        """Create a new board for a HALF project.

        Args:
            title: Board title.
            description: Board description.

        Returns:
            Created board.
        """
        data = {
            "title": title,
            "description": description,
            "team_id": self.team_id,
            "type": "board",  # 'board' or 'template'
        }
        try:
            result = self._request("POST", "/boards", data)
            return FocalboardBoard(
                id=result.get("id", ""),
                title=result.get("title", title),
                description=result.get("description", description),
            )
        except RuntimeError:
            logger.warning("Could not create Focalboard board (offline?)")
            return FocalboardBoard(id="", title=title, description=description)

    def list_boards(self) -> List[FocalboardBoard]:
        """List all boards.

        Returns:
            List of boards.
        """
        try:
            result = self._request("GET", "/boards")
            if isinstance(result, list):
                return [
                    FocalboardBoard(
                        id=b.get("id", ""),
                        title=b.get("title", ""),
                        description=b.get("description", ""),
                    )
                    for b in result
                ]
        except RuntimeError:
            pass
        return []

    # ─── Card / Task Operations ──────────────────────────────────────────

    def create_task(
        self,
        board_id: str,
        title: str,
        description: str = "",
        phase: str = "phase-1",
        priority: str = "medium",
    ) -> FocalboardCard:
        """Create a task card on a board.

        Args:
            board_id: Board ID.
            title: Card title.
            description: Card description.
            phase: HALF phase identifier.
            priority: Task priority (low, medium, high, critical).

        Returns:
            Created card.
        """
        data = {
            "title": title,
            "description": description,
            "board_id": board_id,
            "properties": {
                "phase": phase,
                "priority": priority,
                "status": "open",
            },
        }
        try:
            result = self._request("POST", f"/boards/{board_id}/cards", data)
            return FocalboardCard(
                id=result.get("id", ""),
                title=result.get("title", title),
                description=result.get("description", description),
                status=result.get("properties", {}).get("status", "open"),
                phase=result.get("properties", {}).get("phase", phase),
                priority=result.get("properties", {}).get("priority", priority),
            )
        except RuntimeError:
            logger.warning("Could not create task card (Focalboard offline?)")
            return FocalboardCard(id="", title=title, description=description)

    def update_task_status(self, card_id: str, status: str) -> bool:
        """Update a task card's status.

        Args:
            card_id: Card ID.
            status: New status (open, in-progress, done, blocked).

        Returns:
            True if update succeeded.
        """
        data = {"properties": {"status": status}}
        try:
            self._request("PATCH", f"/cards/{card_id}", data)
            return True
        except RuntimeError:
            return False

    def get_tasks_by_phase(self, board_id: str, phase: str) -> List[FocalboardCard]:
        """Get all tasks for a specific HALF phase.

        Args:
            board_id: Board ID.
            phase: Phase identifier.

        Returns:
            List of cards in that phase.
        """
        try:
            result = self._request("GET", f"/boards/{board_id}/cards")
            if isinstance(result, list):
                return [
                    FocalboardCard(
                        id=c.get("id", ""),
                        title=c.get("title", ""),
                        status=c.get("properties", {}).get("status", "open"),
                        phase=c.get("properties", {}).get("phase", ""),
                        priority=c.get("properties", {}).get("priority", "medium"),
                    )
                    for c in result
                    if c.get("properties", {}).get("phase") == phase
                ]
        except RuntimeError:
            pass
        return []

    @staticmethod
    def task_from_phase_step(
        phase: str,
        step_name: str,
        agent_skill: str,
    ) -> FocalboardCard:
        """Create a HALF phase step as a Focalboard card.

        Args:
            phase: Phase identifier.
            step_name: Human-readable step name.
            agent_skill: Agent skill assigned to this step.

        Returns:
            A FocalboardCard representing this step.
        """
        return FocalboardCard(
            id="",
            title=f"[{phase.upper()}] {step_name}",
            description=f"Assigned to: {agent_skill}",
            status="open",
            phase=phase,
        )

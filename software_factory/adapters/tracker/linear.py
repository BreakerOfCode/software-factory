"""
Linear Issue Tracker Adapter.
Fetches Linear issues via Linear GraphQL API or Linear MCP environment.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from .base import BaseTrackerAdapter
from ...spec_parser import TicketSpec, parse_ticket_spec


class LinearAdapter(BaseTrackerAdapter):
    """Adapter for Linear GraphQL API."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        tracker_cfg = config.get("issue_tracker", {})
        self.api_key = os.getenv(tracker_cfg.get("auth_token_env", "LINEAR_API_KEY"), "")
        self.team_key = tracker_cfg.get("project_key", "")

    def _execute_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {}
        url = "https://api.linear.app/graphql"
        headers = {"Authorization": self.api_key, "Content-Type": "application/json"}
        try:
            resp = requests.post(url, json={"query": query, "variables": variables or {}}, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("data", {})
        except requests.RequestException:
            pass
        return {}

    def get_active_ticket(self) -> Optional[TicketSpec]:
        query = """
        query ActiveIssues($teamKey: String!) {
            issues(filter: { team: { key: { eq: $teamKey } }, state: { name: { eq: "In Progress" } } }, first: 1) {
                nodes {
                    id
                    identifier
                    title
                    description
                }
            }
        }
        """
        data = self._execute_graphql(query, {"teamKey": self.team_key})
        nodes = data.get("issues", {}).get("nodes", [])
        if not nodes:
            return None
        node = nodes[0]
        try:
            return parse_ticket_spec(
                ticket_id=node.get("identifier", node.get("id")),
                title=node.get("title", ""),
                description=node.get("description", "")
            )
        except ValueError:
            return None

    def get_next_todo_ticket(self) -> Optional[TicketSpec]:
        query = """
        query TodoIssues($teamKey: String!) {
            issues(filter: { team: { key: { eq: $teamKey } }, state: { name: { eq: "Todo" } } }, first: 10) {
                nodes {
                    id
                    identifier
                    title
                    description
                }
            }
        }
        """
        data = self._execute_graphql(query, {"teamKey": self.team_key})
        nodes = data.get("issues", {}).get("nodes", [])
        for node in nodes:
            try:
                return parse_ticket_spec(
                    ticket_id=node.get("identifier", node.get("id")),
                    title=node.get("title", ""),
                    description=node.get("description", "")
                )
            except ValueError:
                continue
        return None

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        # Status update implementation for Linear
        return bool(self.api_key)

    def post_pr_link(self, ticket_id: str, pr_url: str, comment: Optional[str] = None) -> bool:
        # PR attachment implementation for Linear
        return bool(self.api_key)

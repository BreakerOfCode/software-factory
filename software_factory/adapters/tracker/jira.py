"""
Jira Issue Tracker Adapter.
Fetches JIRA issues via REST API using JQL and parses 5-part specs (Markdown or FrontMatter).
"""

import os
import requests
from typing import Optional, Dict, Any, List
from .base import BaseTrackerAdapter
from ...spec_parser import TicketSpec, parse_ticket_spec


class JiraAdapter(BaseTrackerAdapter):
    """Adapter for Atlassian Jira Cloud REST API."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        tracker_cfg = config.get("issue_tracker", {})
        self.domain = os.getenv(tracker_cfg.get("domain_env", "JIRA_DOMAIN"), "")
        self.email = os.getenv(tracker_cfg.get("auth_email_env", "JIRA_EMAIL"), "")
        self.api_token = os.getenv(tracker_cfg.get("auth_token_env", "JIRA_API_TOKEN"), "")
        self.project_key = tracker_cfg.get("project_key", "")
        self.jql_override = tracker_cfg.get("jql_query", "")

    def _get_auth(self) -> Optional[tuple[str, str]]:
        if self.email and self.api_token:
            return (self.email, self.api_token)
        return None

    def _get_base_url(self) -> str:
        domain = self.domain.rstrip("/")
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        return f"{domain}/rest/api/3"

    def _execute_jql(self, jql: str) -> List[Dict[str, Any]]:
        auth = self._get_auth()
        if not auth or not self.domain:
            # Fallback for dry run / unconfigured environment
            return []

        url = f"{self._get_base_url()}/search"
        headers = {"Accept": "application/json"}
        params = {"jql": jql, "maxResults": 10, "fields": "summary,description,status,issuelinks"}
        
        try:
            resp = requests.get(url, headers=headers, auth=auth, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("issues", [])
        except requests.RequestException:
            pass
        return []

    def get_active_ticket(self) -> Optional[TicketSpec]:
        """Finds any ticket in 'In Progress' status for the project."""
        jql = f"project = {self.project_key} AND status = 'In Progress' ORDER BY updated DESC"
        issues = self._execute_jql(jql)
        if not issues:
            return None
        
        issue = issues[0]
        return self._convert_issue_to_spec(issue)

    def get_next_todo_ticket(self) -> Optional[TicketSpec]:
        """Finds top unblocked 'To Do' ticket."""
        if self.jql_override:
            jql = self.jql_override
        else:
            jql = f"project = {self.project_key} AND status = 'To Do' AND issueLinkType != 'is blocked by' ORDER BY rank ASC"
        
        issues = self._execute_jql(jql)
        for issue in issues:
            # Verify no open blocking links
            links = issue.get("fields", {}).get("issuelinks", [])
            has_open_blocker = False
            for link in links:
                if link.get("type", {}).get("name") == "Blocks":
                    inward = link.get("inwardIssue", {})
                    if inward and inward.get("fields", {}).get("status", {}).get("name") != "Done":
                        has_open_blocker = True
                        break
            if not has_open_blocker:
                spec = self._convert_issue_to_spec(issue)
                if spec:
                    return spec
        return None

    def _convert_issue_to_spec(self, issue: Dict[str, Any]) -> Optional[TicketSpec]:
        ticket_id = issue.get("key", "")
        fields = issue.get("fields", {})
        title = fields.get("summary", "")
        
        # Raw text or Atlassian Document Format rendering
        raw_desc = fields.get("description", "")
        if isinstance(raw_desc, dict):
            # Extract plain text from ADF nodes
            desc_text = self._extract_adf_text(raw_desc)
        else:
            desc_text = str(raw_desc or "")

        try:
            return parse_ticket_spec(ticket_id=ticket_id, title=title, description=desc_text)
        except ValueError:
            return None

    def _extract_adf_text(self, node: Dict[str, Any]) -> str:
        """Helper to extract text from Atlassian Document Format JSON trees."""
        text_parts = []
        node_type = node.get("type")
        if node_type == "text":
            return node.get("text", "")
        elif node_type == "heading":
            level = node.get("attrs", {}).get("level", 2)
            heading_str = "#" * level
            content_text = "".join(self._extract_adf_text(child) for child in node.get("content", []))
            return f"\n{heading_str} {content_text}\n"
        
        content = node.get("content", [])
        for child in content:
            text_parts.append(self._extract_adf_text(child))
        return "".join(text_parts)

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        auth = self._get_auth()
        if not auth or not self.domain:
            return False

        # Transition endpoint
        url = f"{self._get_base_url()}/issue/{ticket_id}/transitions"
        try:
            # Fetch available transitions
            resp = requests.get(url, auth=auth, timeout=10)
            if resp.status_code != 200:
                return False
            
            transitions = resp.json().get("transitions", [])
            target_trans = next((t for t in transitions if t.get("name", "").lower() == status.lower()), None)
            if not target_trans:
                return False

            payload = {"transition": {"id": target_trans["id"]}}
            post_resp = requests.post(url, json=payload, auth=auth, timeout=10)
            return post_resp.status_code == 204
        except requests.RequestException:
            return False

    def post_pr_link(self, ticket_id: str, pr_url: str, comment: Optional[str] = None) -> bool:
        auth = self._get_auth()
        if not auth or not self.domain:
            return False

        url = f"{self._get_base_url()}/issue/{ticket_id}/comment"
        body_text = f"PR Opened into integration branch: {pr_url}"
        if comment:
            body_text += f"\n\n{comment}"

        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": body_text}]
                    }
                ]
            }
        }
        try:
            resp = requests.post(url, json=payload, auth=auth, timeout=10)
            return resp.status_code == 201
        except requests.RequestException:
            return False

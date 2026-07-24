"""
Local Markdown Issue Tracker Adapter.
Reads local 5-part ticket spec files from a `.factory/backlog/` directory.
"""

import os
import glob
from typing import Optional, Dict, Any, List
from .base import BaseTrackerAdapter
from ...spec_parser import TicketSpec, parse_ticket_spec


class LocalMdAdapter(BaseTrackerAdapter):
    """Adapter for local filesystem Markdown tickets."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.backlog_dir = config.get("issue_tracker", {}).get("backlog_dir", ".factory/backlog")

    def _get_files(self, status: str) -> List[str]:
        target_dir = os.path.join(self.backlog_dir, status)
        if not os.path.exists(target_dir):
            return []
        return sorted(glob.glob(os.path.join(target_dir, "*.md")))

    def get_active_ticket(self) -> Optional[TicketSpec]:
        files = self._get_files("in_progress")
        if not files:
            return None
        filepath = files[0]
        filename = os.path.basename(filepath)
        ticket_id = filename.replace(".md", "").upper()
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        try:
            return parse_ticket_spec(ticket_id=ticket_id, title=ticket_id, description=content)
        except ValueError:
            return None

    def get_next_todo_ticket(self) -> Optional[TicketSpec]:
        files = self._get_files("todo")
        for filepath in files:
            filename = os.path.basename(filepath)
            ticket_id = filename.replace(".md", "").upper()
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            try:
                return parse_ticket_spec(ticket_id=ticket_id, title=ticket_id, description=content)
            except ValueError:
                continue
        return None

    def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        # Move file between todo / in_progress / in_review / done folders
        src_files = glob.glob(os.path.join(self.backlog_dir, "*", f"{ticket_id.lower()}.md"))
        if not src_files:
            return False
        
        src_path = src_files[0]
        dest_dir = os.path.join(self.backlog_dir, status.lower().replace(" ", "_"))
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        
        os.rename(src_path, dest_path)
        return True

    def post_pr_link(self, ticket_id: str, pr_url: str, comment: Optional[str] = None) -> bool:
        src_files = glob.glob(os.path.join(self.backlog_dir, "*", f"{ticket_id.lower()}.md"))
        if not src_files:
            return False
        with open(src_files[0], "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n**PR Link**: {pr_url}\n")
            if comment:
                f.write(f"{comment}\n")
        return True

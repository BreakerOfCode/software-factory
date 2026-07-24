"""
5-Part Ticket Spec Parser for Software Factory.
Extracts strongly typed specs (Goal, Target Files, Interface Contract, Requirements, Definition of Done)
from Markdown descriptions or YAML FrontMatter in Jira, Linear, or Local files.
"""

import re
import yaml
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TicketSpec(BaseModel):
    ticket_id: str
    title: str
    goal: str = Field(description="One-line summary of what this component does")
    target_files: List[str] = Field(description="Explicit list of files to modify or create")
    interface_contract: str = Field(default="", description="Expected input/output signatures or Pydantic models")
    requirements: List[str] = Field(default_factory=list, description="Numbered behavioral constraints")
    definition_of_done: List[str] = Field(default_factory=list, description="Verification checklist items")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Parsed frontmatter or extra ticket metadata")

    @field_validator("target_files")
    @classmethod
    def validate_target_files(cls, v: List[str]) -> List[str]:
        cleaned = [f.strip(" `*-\t") for f in v if f.strip(" `*-\t")]
        if not cleaned:
            raise ValueError("Ticket is INVALID: Target Files list cannot be empty or missing.")
        return cleaned


def parse_frontmatter(text: str) -> tuple[Dict[str, Any], str]:
    """Parses optional YAML frontmatter from markdown text."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        raw_yaml = match.group(1)
        body = text[match.end():]
        try:
            parsed = yaml.safe_load(raw_yaml) or {}
            return parsed if isinstance(parsed, dict) else {}, body
        except yaml.YAMLError:
            return {}, body
    return {}, text


def parse_ticket_spec(ticket_id: str, title: str, description: str) -> TicketSpec:
    """
    Parses a raw issue description into a validated TicketSpec object.
    Supports both Markdown sections (e.g. ## Goal, ## Target Files) and FrontMatter.
    """
    metadata, body = parse_frontmatter(description)

    # If frontmatter supplies spec keys directly, use them
    if "goal" in metadata and "target_files" in metadata:
        target_files = metadata.get("target_files", [])
        if isinstance(target_files, str):
            target_files = [target_files]
        
        reqs = metadata.get("requirements", [])
        if isinstance(reqs, str):
            reqs = [reqs]
            
        dod = metadata.get("definition_of_done", [])
        if isinstance(dod, str):
            dod = [dod]

        return TicketSpec(
            ticket_id=ticket_id,
            title=title,
            goal=str(metadata.get("goal", title)),
            target_files=target_files,
            interface_contract=str(metadata.get("interface_contract", "")),
            requirements=reqs,
            definition_of_done=dod,
            metadata=metadata,
        )

    # Otherwise parse H2/H3 markdown headings
    headings = re.split(r"(?m)^#{2,3}\s+", body)
    
    sections: Dict[str, str] = {}
    for block in headings:
        lines = block.strip().split("\n")
        if not lines:
            continue
        heading_name = lines[0].strip().lower()
        content = "\n".join(lines[1:]).strip()
        sections[heading_name] = content

    goal = sections.get("goal", title)
    
    # Target files extraction from bullet lists or code blocks
    raw_targets = sections.get("target files", "") or sections.get("target_files", "")
    target_files = []
    for line in raw_targets.split("\n"):
        line = line.strip()
        if line.startswith("-") or line.startswith("*") or line.startswith("`"):
            cleaned = line.lstrip("-* `").rstrip("`")
            if cleaned and not cleaned.startswith("#"):
                target_files.append(cleaned)

    # Interface contract
    interface_contract = sections.get("interface contract", "") or sections.get("interface_contract", "")

    # Requirements
    raw_reqs = sections.get("requirements", "")
    requirements = [
        re.sub(r"^\d+[\.\)]\s*|^[-\*]\s*", "", line).strip()
        for line in raw_reqs.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]

    # Definition of Done
    raw_dod = sections.get("definition of done", "") or sections.get("definition_of_done", "")
    definition_of_done = [
        re.sub(r"^-\s*\[[ xX]\]\s*|^[-\*]\s*", "", line).strip()
        for line in raw_dod.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]

    return TicketSpec(
        ticket_id=ticket_id,
        title=title,
        goal=goal,
        target_files=target_files,
        interface_contract=interface_contract,
        requirements=requirements,
        definition_of_done=definition_of_done,
        metadata=metadata,
    )

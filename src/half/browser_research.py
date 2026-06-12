"""HALF — Browser-Use Web Research Agent (Phase 1).

Enables agents to autonomously fetch web content, research topics,
and resolve missing technical constraints during Discovery & Strategy.
"""

from __future__ import annotations

import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger("half.browser_use")


class BrowserResearchAgent:
    """Web research agent for Phase 1 Discovery & Strategy."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._history: list[dict[str, Any]] = []

    def fetch_url(self, url: str, timeout: int = 15) -> dict[str, Any]:
        """Fetch content from a URL.

        Args:
            url: The URL to fetch.
            timeout: Request timeout in seconds.

        Returns:
            Dict with text content and metadata.
        """
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "HALF-Research/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                # Strip HTML tags for plain text
                text = re.sub(r"<[^>]+>", " ", content)
                text = re.sub(r"\s+", " ", text).strip()[:5000]
                return {
                    "url": url,
                    "status": resp.status,
                    "content_length": len(content),
                    "text": text[:2000],
                    "success": True,
                }
        except urllib.error.HTTPError as e:
            return {"url": url, "error": f"HTTP {e.code}: {e.reason}", "success": False}
        except urllib.error.URLError as e:
            return {
                "url": url,
                "error": f"Connection failed: {e.reason}",
                "success": False,
            }
        except Exception as e:
            return {"url": url, "error": str(e), "success": False}

    def research_topic(self, topic: str, max_pages: int = 3) -> list[dict[str, Any]]:
        """Research a topic by fetching relevant URLs.

        Args:
            topic: The topic to research.
            max_pages: Maximum pages to visit.

        Returns:
            List of research findings.
        """
        logger.info("Researching topic: %s", topic)
        findings = []

        search_urls = [
            f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(topic)}",
        ]

        pages_fetched = 0
        for url in search_urls:
            if pages_fetched >= max_pages:
                break
            result = self.fetch_url(url)
            if result.get("success"):
                pages_fetched += 1
            findings.append(result)

        finding = {
            "topic": topic,
            "sources_checked": pages_fetched,
            "findings": findings,
            "confidence": "HIGH" if pages_fetched > 0 else "LOW",
            "needs_human_review": pages_fetched == 0,
        }
        self._history.append(finding)
        return findings

    def scrape_documentation(self, url: str) -> dict[str, Any]:
        """Scrape documentation from a URL."""
        result = self.fetch_url(url)
        if result.get("success"):
            logger.info(
                "Documentation fetched: %s (%d chars)",
                url,
                result.get("content_length", 0),
            )
        else:
            logger.warning(
                "Documentation fetch failed: %s — %s", url, result.get("error")
            )
        return result

    def compare_technologies(
        self, options: list[str], criteria: list[str]
    ) -> dict[str, Any]:
        """Compare multiple technologies by researching each."""
        comparison: dict[str, Any] = {
            "options": options,
            "criteria": criteria,
            "matrix": {},
            "recommendation": "",
        }
        for opt in options:
            comparison["matrix"][opt] = dict.fromkeys(criteria, "TBD")
            # Try to fetch info about each option
            result = self.fetch_url(
                f"https://duckduckgo.com/html/?q={urllib.parse.quote(opt + ' documentation')}"
            )
            if result.get("success"):
                comparison["matrix"][opt]["documentation_found"] = (
                    "Yes" if result.get("text") else "No"
                )

        logger.info("Compared %d technologies", len(options))
        return comparison

    def generate_adr_from_research(
        self, title: str, context: str, options: list[str], decision: str
    ) -> str:
        """Generate an Architecture Decision Record from research data."""
        lines = [
            f"# ADR: {title}",
            "",
            "## Context",
            context,
            "",
            "## Options Considered",
        ]
        for i, opt in enumerate(options, 1):
            lines.append(f"{i}. {opt}")
        lines.extend(
            [
                "",
                "## Decision",
                decision,
                "",
                "## Status",
                "Proposed",
                "",
                "## Consequences",
                "- Research-backed decision",
                "- See research history for detailed analysis",
            ]
        )
        return "\n".join(lines)

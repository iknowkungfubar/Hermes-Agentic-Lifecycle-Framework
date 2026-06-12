"""HALF — Portable Skill Modules (PSM) Infrastructure.

PSMs are version-controlled markdown and script bundles placed into
.harness/skills/ that enable HALF to acquire external capabilities.
Uses the agentskills.io standard for discoverability.

Based on the HALF doctrine's 'Portable Skill Modules' specification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("half.psm")


@dataclass
class PortableSkillModule:
    """A Portable Skill Module following agentskills.io standard."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = "HALF"
    license: str = "MIT"
    entrypoint: str = ""  # Path to the main script
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    loaded: bool = False
    path: str = ""


SKILL_REGISTRY_URLS = {
    "browser-use": "https://raw.githubusercontent.com/nickscamara/browser-use-agent/main/skill.yaml",
    "financial-data": "https://raw.githubusercontent.com/agentskills/financial-data/main/skill.yaml",
    "legal-document-generation": "https://raw.githubusercontent.com/agentskills/legal-docs/main/skill.yaml",
    "data-analysis-pandas": "https://raw.githubusercontent.com/agentskills/data-analysis/main/skill.yaml",
    "media-synthesis": "https://raw.githubusercontent.com/agentskills/media-synthesis/main/skill.yaml",
}


class PSMManager:
    """Manages Portable Skill Modules in .harness/skills/.

    Discovers, loads, and validates PSMs from the local filesystem
    or remote registries (agentskills.io).
    """

    def __init__(self, skills_dir: str | Path = ".harness/skills"):
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._modules: dict[str, PortableSkillModule] = {}

    def discover(self) -> list[PortableSkillModule]:
        """Discover all PSMs in the skills directory.

        Returns:
            List of discovered modules.
        """
        self._modules = {}
        for yaml_file in self.skills_dir.glob("*.yaml"):
            module = self._load_skill_file(yaml_file)
            if module:
                self._modules[module.name] = module

        for yml_file in self.skills_dir.glob("*.yml"):
            if yml_file.stem not in self._modules:
                module = self._load_skill_file(yml_file)
                if module:
                    self._modules[module.name] = module

        # Also load markdown skills
        for md_file in self.skills_dir.glob("*.md"):
            if md_file.stem not in self._modules:
                module = self._load_markdown_skill(md_file)
                if module:
                    self._modules[module.name] = module

        logger.info(
            "PSM: Discovered %d modules in %s", len(self._modules), self.skills_dir
        )
        return list(self._modules.values())

    def _load_skill_file(self, yaml_path: Path) -> PortableSkillModule | None:
        """Load a YAML skill definition."""
        try:
            import yaml

            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            if not data or "name" not in data:
                return None
            return PortableSkillModule(
                name=data["name"],
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                author=data.get("author", "unknown"),
                license=data.get("license", "MIT"),
                entrypoint=data.get("entrypoint", ""),
                dependencies=data.get("dependencies", []),
                tags=data.get("tags", []),
                path=str(yaml_path),
            )
        except Exception as e:
            logger.warning("PSM: Failed to load %s: %s", yaml_path, e)
            return None

    def _load_markdown_skill(self, md_path: Path) -> PortableSkillModule | None:
        """Load a markdown skill definition (extracts frontmatter)."""
        try:
            content = md_path.read_text()
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    import yaml

                    data = yaml.safe_load(frontmatter)
                    if data and "name" in data:
                        return PortableSkillModule(
                            name=data["name"],
                            version=data.get("version", "1.0.0"),
                            description=data.get("description", ""),
                            author=data.get("author", "unknown"),
                            license=data.get("license", "MIT"),
                            tags=data.get("tags", []),
                            path=str(md_path),
                        )
        except Exception as e:
            logger.warning("PSM: Failed to parse %s: %s", md_path, e)
        return None

    def install(self, skill_name: str) -> PortableSkillModule | None:
        """Install a skill from the agentskills.io registry.

        Args:
            skill_name: The skill name to install.

        Returns:
            The installed module, or None if not found.
        """
        url = SKILL_REGISTRY_URLS.get(skill_name)
        if not url:
            logger.warning("PSM: Unknown skill '%s'", skill_name)
            return None

        target = self.skills_dir / f"{skill_name}.yaml"
        try:
            import urllib.request

            logger.info("PSM: Downloading '%s' from %s", skill_name, url)
            urllib.request.urlretrieve(url, target)
            module = self._load_skill_file(target)
            if module:
                self._modules[module.name] = module
                logger.info(
                    "PSM: Installed skill '%s' v%s", module.name, module.version
                )
                return module
        except Exception as e:
            logger.warning("PSM: Failed to install '%s': %s", skill_name, e)

        # Fallback: create a stub skill definition
        stub = self._create_stub_skill(skill_name)
        if stub:
            self._modules[stub.name] = stub
        return stub

    def _create_stub_skill(self, name: str) -> PortableSkillModule:
        """Create a local stub skill when registry download fails."""
        module = PortableSkillModule(
            name=name,
            description=f"Local stub for '{name}' — install from agentskills.io for full functionality",
            tags=[name],
            path=str(self.skills_dir / f"{name}.md"),
        )
        stub_path = self.skills_dir / f"{name}.md"
        if not stub_path.exists():
            stub_path.write_text(
                f"---\n"
                f"name: {name}\n"
                f'version: "1.0.0"\n'
                f'description: "Stub for {name} — install from agentskills.io"\n'
                f"---\n\n"
                f"# {name}\n\n"
                f"To install the full version:\n"
                f"```bash\n"
                f"# Download from https://agentskills.io/{name}\n"
                f"```\n"
            )
        logger.info("PSM: Created stub for '%s'", name)
        return module

    def get_module(self, name: str) -> PortableSkillModule | None:
        """Get a loaded module by name.

        Args:
            name: Module name.

        Returns:
            The module if loaded, None otherwise.
        """
        return self._modules.get(name)

    def list_modules(self) -> list[dict[str, str]]:
        """List all loaded modules.

        Returns:
            List of module summaries.
        """
        return [
            {"name": m.name, "version": m.version, "description": m.description[:60]}
            for m in self._modules.values()
        ]

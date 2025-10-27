"""Test to ensure no production data leaked into the repository.

This test loads actual production XML files, extracts all sensitive data
(VN numbers, names, birth dates, addresses, etc.), and then scans the
entire repository to ensure none of those specific values appear anywhere.

CRITICAL for GDPR compliance and protecting Swiss citizens' privacy.
"""

import re
from pathlib import Path
from typing import Set
import xml.etree.ElementTree as ET

import pytest


class TestNoProductionDataLeakage:
    """Verify no production personal data leaked into repository."""

    def test_no_production_data_in_repository(self, production_data_path, skip_if_no_production_data):
        """Scan repository for any values from production data files.

        This test:
        1. Loads all production XML files
        2. Extracts sensitive data: VN numbers, names, birth dates, addresses
        3. Scans entire repository (code, tests, docs) for these values
        4. Fails if any production value is found

        Requires production data to be configured via config.yaml or env var.
        """
        project_root = Path(__file__).parent.parent

        # Step 1: Extract all sensitive values from production data
        print("\n📂 Loading production data...")
        sensitive_values = self._extract_sensitive_data_from_production(production_data_path)

        if not sensitive_values:
            pytest.skip("No production data found to check against")

        print(f"✓ Extracted {len(sensitive_values)} sensitive values from production data")

        # Step 2: Scan repository files for these specific values
        print("🔍 Scanning repository files for production data leakage...")
        file_violations = self._scan_repository_for_values(project_root, sensitive_values, production_data_path)

        # Step 3: Scan git commit messages for these specific values
        print("🔍 Scanning git commit messages for production data leakage...")
        commit_violations = self._scan_git_commits_for_values(project_root, sensitive_values)

        # Step 4: Report violations
        all_violations = file_violations + commit_violations
        if all_violations:
            msg = self._format_violation_report(file_violations, commit_violations)
            raise AssertionError(msg)

        print("✅ No production data leakage detected in files or commit messages!")

    def _extract_sensitive_data_from_production(self, prod_dir: Path) -> Set[str]:
        """Extract all sensitive data from production XML files.

        Returns:
            Set of sensitive strings found in production data
        """
        sensitive_values = set()

        # Find all XML files
        xml_files = list(prod_dir.glob("*.xml"))

        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Extract text from all elements
                for elem in root.iter():
                    if elem.text and elem.text.strip():
                        text = elem.text.strip()

                        # Filter out generic/synthetic values
                        if self._is_potentially_sensitive(text):
                            sensitive_values.add(text)

                    # Also check attributes
                    for attr_value in elem.attrib.values():
                        if attr_value and attr_value.strip():
                            attr_text = attr_value.strip()
                            if self._is_potentially_sensitive(attr_text):
                                sensitive_values.add(attr_text)

            except Exception as e:
                # Skip files that can't be parsed
                print(f"  ⚠️  Could not parse {xml_file.name}: {e}")
                continue

        return sensitive_values

    def _is_potentially_sensitive(self, text: str) -> bool:
        """Determine if a text value is potentially sensitive PERSONAL data.

        Only flags data that could identify specific individuals, NOT public reference data.
        """
        # Skip very short strings
        if len(text) < 3:
            return False

        # Skip common XML/generic values
        generic_values = {
            'true', 'false', 'yes', 'no', 'null', 'none',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
        }
        if text.lower() in generic_values:
            return False

        # Skip country codes (ISO 2-letter codes)
        if re.match(r'^[A-Z]{2}$', text):
            return False

        # Skip 4-digit codes (BFS municipality/country codes - these are public)
        if re.match(r'^\d{4}$', text):
            return False

        # Skip canton codes (2 uppercase letters)
        if re.match(r'^[A-Z]{2}$', text):
            return False

        # ONLY include if it's:
        # 1. VN number (13 digits) - TRULY SENSITIVE!
        if re.match(r'^\d{13}$', text):
            return True

        # 2. Full person names with first AND last name (two words with capitals)
        # Skip single words (likely municipality names like "Bern", "Zürich")
        if re.match(r'^[A-ZÄÖÜ][a-zäöüéèêàâ]+\s+[A-ZÄÖÜ][a-zäöüéèêàâ]+', text):
            return True

        # 3. Full birth dates (YYYY-MM-DD with specific day, not just year)
        if re.match(r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$', text):
            return True

        # 4. Street addresses with house numbers (e.g., "Hauptstrasse 15")
        # But NOT municipality names
        if re.match(r'^[A-ZÄÖÜ][a-zäöüéèêàâ]+\s+\d+[a-z]?$', text):
            return True

        return False

    def _scan_repository_for_values(
        self,
        project_root: Path,
        sensitive_values: Set[str],
        prod_dir: Path
    ) -> list:
        """Scan repository for any of the sensitive values.

        Returns:
            List of (file_path, line_num, value) tuples for violations
        """
        violations = []

        # Directories to exclude
        exclude_dirs = {'.git', 'venv', '__pycache__', '.pytest_cache',
                       'node_modules', '.tox', 'build', 'dist', '.eggs'}

        # File extensions to scan
        text_extensions = {'.py', '.md', '.rst', '.txt', '.yml', '.yaml',
                          '.toml', '.json', '.cfg', '.ini', ''}

        for file_path in project_root.rglob('*'):
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue

            # Skip the production data directory itself!
            try:
                file_path.relative_to(prod_dir)
                continue  # This file is in production data dir, skip it
            except ValueError:
                pass  # Not in production dir, continue scanning

            # Only scan text files
            if not file_path.is_file():
                continue

            if file_path.suffix not in text_extensions:
                continue

            # Skip this test file itself
            if file_path.name == 'test_no_production_data_leakage.py':
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            # Check for each sensitive value
            for value in sensitive_values:
                if value in content:
                    # Find line number
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        if value in line:
                            violations.append((
                                str(file_path.relative_to(project_root)),
                                line_num,
                                value
                            ))

        return violations

    def _scan_git_commits_for_values(
        self,
        project_root: Path,
        sensitive_values: Set[str]
    ) -> list:
        """Scan git commit messages for any of the sensitive values.

        Returns:
            List of (commit_hash, value) tuples for violations
        """
        violations = []

        try:
            import subprocess

            # Get all commit messages (subject + body)
            result = subprocess.run(
                ['git', 'log', '--all', '--pretty=format:%H|||%s%n%b%n---END---'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"  ⚠️  Could not read git history: {result.stderr}")
                return violations

            commits_text = result.stdout

            # Parse commits
            commit_blocks = commits_text.split('---END---')

            for block in commit_blocks:
                if not block.strip():
                    continue

                parts = block.split('|||', 1)
                if len(parts) != 2:
                    continue

                commit_hash = parts[0].strip()
                commit_message = parts[1].strip()

                # Check for each sensitive value in commit message
                for value in sensitive_values:
                    if value in commit_message:
                        violations.append((
                            commit_hash[:8],  # Short hash
                            value
                        ))

        except Exception as e:
            print(f"  ⚠️  Could not scan git history: {e}")

        return violations

    def _format_violation_report(self, file_violations: list, commit_violations: list) -> str:
        """Format violation report for assertion message."""
        msg = "\n🚨 CRITICAL: Production data leaked into repository!\n\n"

        # Report file violations
        if file_violations:
            msg += "FILES containing actual values from production XML:\n\n"

            # Group by file
            violations_by_file = {}
            for file_path, line_num, value in file_violations:
                if file_path not in violations_by_file:
                    violations_by_file[file_path] = []
                violations_by_file[file_path].append((line_num, value))

            for file_path, file_viols in violations_by_file.items():
                msg += f"  📄 {file_path}\n"
                for line_num, value in file_viols[:5]:  # Show max 5 per file
                    # Mask value for security in test output
                    masked = value[:3] + "*" * (len(value) - 3) if len(value) > 3 else "***"
                    msg += f"     Line {line_num}: {masked}\n"
                if len(file_viols) > 5:
                    msg += f"     ... and {len(file_viols) - 5} more\n"
                msg += "\n"

        # Report commit message violations
        if commit_violations:
            msg += "\nGIT COMMIT MESSAGES containing production data:\n\n"

            # Group by commit
            violations_by_commit = {}
            for commit_hash, value in commit_violations:
                if commit_hash not in violations_by_commit:
                    violations_by_commit[commit_hash] = []
                violations_by_commit[commit_hash].append(value)

            for commit_hash, values in violations_by_commit.items():
                msg += f"  🔴 Commit {commit_hash}\n"
                for value in values[:5]:  # Show max 5 per commit
                    masked = value[:3] + "*" * (len(value) - 3) if len(value) > 3 else "***"
                    msg += f"     Contains: {masked}\n"
                if len(values) > 5:
                    msg += f"     ... and {len(values) - 5} more\n"
                msg += "\n"

        msg += (
            "\n⚠️  GDPR VIOLATION RISK!\n"
            "These values come from real Swiss government data.\n\n"
            "Action required:\n"
            "1. Remove these values from files immediately\n"
            "2. Use synthetic test data only\n"
            "3. Never hardcode production values in examples\n"
        )

        if commit_violations:
            msg += (
                "4. 🚨 CRITICAL: Git history contains sensitive data!\n"
                "   - Use 'git filter-repo' or 'BFG Repo-Cleaner' to purge commits\n"
                "   - Notify all users to re-clone the repository\n"
                "   - Force-push cleaned history (coordinate with team!)\n"
            )
        else:
            msg += "4. Review git history for other potential issues\n"

        return msg


if __name__ == "__main__":
    # Run test when executed directly (requires pytest fixtures)
    pytest.main([__file__, "-v"])

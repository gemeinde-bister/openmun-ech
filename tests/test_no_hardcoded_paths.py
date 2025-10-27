"""Test to ensure no hardcoded paths leak into the library code.

This test scans the library folder (excluding tests/ and docs) to ensure
no absolute paths or sensitive data paths are hardcoded in the source code.
"""

import re
from pathlib import Path


class TestNoHardcodedPaths:
    """Verify no hardcoded paths in library source code."""

    def test_no_hardcoded_paths_in_library(self):
        """Scan library folder for hardcoded paths that could leak sensitive data.

        This test ensures that:
        - No absolute paths like /home/kab/... are in library code
        - No hardcoded production data paths exist
        - Configuration is properly externalized

        Excluded from scan:
        - tests/ directory (test fixtures are allowed to reference test data)
        - Config files (config.yaml - gitignored anyway)
        - .git, venv, __pycache__ directories
        - This test file itself
        """
        project_root = Path(__file__).parent.parent
        hardcoded_patterns = [
            r'/home/\w+',  # Absolute home paths
            r'/Users/\w+',  # macOS home paths
            r'C:\\Users\\',  # Windows paths
            r'/Documents/',  # Common personal directories
            r'bister/sedex',  # Project-specific sensitive path
        ]

        # Directories to exclude
        exclude_dirs = {'.git', 'venv', '__pycache__', '.pytest_cache',
                       'tests', 'node_modules', '.tox', 'build', 'dist'}

        # File extensions to scan
        scan_extensions = {'.py', '.md', '.rst', '.txt', '.yml', '.yaml', '.toml', ''}

        violations = []

        # Scan all files in repository (except excluded)
        for file_path in project_root.rglob('*'):
            # Skip excluded directories
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue

            # Skip config.yaml (it's gitignored)
            if file_path.name == 'config.yaml':
                continue

            # Skip this test file itself
            if file_path.name == 'test_no_hardcoded_paths.py':
                continue

            # Only scan text files
            if not file_path.is_file():
                continue

            if file_path.suffix not in scan_extensions:
                continue

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            for pattern in hardcoded_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1
                    violations.append(
                        f"{file_path.relative_to(project_root)}:{line_num} - "
                        f"Found hardcoded path: {match.group()}"
                    )

        # Report violations
        if violations:
            msg = (
                "\n❌ Found hardcoded paths in library code!\n\n"
                "The following files contain hardcoded paths that should be externalized:\n\n"
            )
            msg += "\n".join(f"  • {v}" for v in violations)
            msg += (
                "\n\n💡 Use config.yaml or environment variables instead.\n"
                "   See config.yaml.sample for configuration options."
            )
            raise AssertionError(msg)


if __name__ == "__main__":
    # Run test when executed directly
    test = TestNoHardcodedPaths()
    try:
        test.test_no_hardcoded_paths_in_library()
        print("✅ No hardcoded paths found in library code!")
    except AssertionError as e:
        print(str(e))
        exit(1)

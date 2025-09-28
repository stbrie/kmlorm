#!/usr/bin/env python3
"""
Automated conversion tool for unittest to pytest patterns.

This script converts unittest.TestCase classes to pure pytest patterns,
handling common assertion patterns and setUp/tearDown methods.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple


class UnittestToPytestConverter:
    """Convert unittest patterns to pytest patterns."""

    # Mapping of unittest assertions to pytest assertions
    ASSERTION_MAPPINGS = {
        r'self\.assertEqual\(([^,]+),\s*([^)]+)\)': r'assert \1 == \2',
        r'self\.assertNotEqual\(([^,]+),\s*([^)]+)\)': r'assert \1 != \2',
        r'self\.assertTrue\(([^)]+)\)': r'assert \1',
        r'self\.assertFalse\(([^)]+)\)': r'assert not \1',
        r'self\.assertIsNone\(([^)]+)\)': r'assert \1 is None',
        r'self\.assertIsNotNone\(([^)]+)\)': r'assert \1 is not None',
        r'self\.assertIn\(([^,]+),\s*([^)]+)\)': r'assert \1 in \2',
        r'self\.assertNotIn\(([^,]+),\s*([^)]+)\)': r'assert \1 not in \2',
        r'self\.assertGreater\(([^,]+),\s*([^)]+)\)': r'assert \1 > \2',
        r'self\.assertLess\(([^,]+),\s*([^)]+)\)': r'assert \1 < \2',
        r'self\.assertGreaterEqual\(([^,]+),\s*([^)]+)\)': r'assert \1 >= \2',
        r'self\.assertLessEqual\(([^,]+),\s*([^)]+)\)': r'assert \1 <= \2',
    }

    # Special patterns that need more complex handling
    SPECIAL_PATTERNS = {
        'assertAlmostEqual': r'self\.assertAlmostEqual\(([^,]+),\s*([^,]+)(?:,\s*places=(\d+))?(?:,\s*delta=([^)]+))?\)',
        'assertRaises': r'with self\.assertRaises\(([^)]+)\):',
        'assertRaisesRegex': r'self\.assertRaisesRegex\(([^,]+),\s*([^,]+),\s*([^)]+)\)',
    }

    def __init__(self, file_path: Path):
        """Initialize converter with file path."""
        self.file_path = file_path
        self.content = file_path.read_text(encoding='utf-8')
        self.lines = self.content.splitlines()
        self.imports_to_add = set()
        self.imports_to_remove = set()

    def convert(self) -> str:
        """Convert unittest patterns to pytest patterns."""
        print(f"Converting {self.file_path.name}...")

        # Process line by line
        converted_lines = []
        in_class = False
        class_indent = 0

        for i, line in enumerate(self.lines):
            # Track if we're in a test class
            if re.match(r'^class.*unittest\.TestCase.*:', line):
                in_class = True
                class_indent = len(line) - len(line.lstrip())
                # Remove unittest.TestCase inheritance
                line = re.sub(r'\(unittest\.TestCase\)', '', line)
                converted_lines.append(line)
                continue
            elif line.strip() and not line.startswith(' ') and in_class:
                in_class = False

            # Convert imports
            if line.strip() == 'import unittest':
                self.imports_to_remove.add('import unittest')
                self.imports_to_add.add('import pytest')
                continue
            elif 'unittest' in line and 'import' in line:
                # Keep other unittest imports (like unittest.mock)
                if not 'unittest.TestCase' in line:
                    converted_lines.append(line)
                continue

            # Convert setUp to fixture
            if re.match(r'    def setUp\(self\)', line):
                line = self._convert_setup_to_fixture(i)

            # Convert tearDown to fixture cleanup
            elif re.match(r'    def tearDown\(self\)', line):
                line = self._convert_teardown_to_fixture(i)

            # Convert assertions
            line = self._convert_assertions(line)

            # Convert self.assertRaises patterns
            line = self._convert_assert_raises(line)

            # Convert assertAlmostEqual
            line = self._convert_assert_almost_equal(line)

            converted_lines.append(line)

        # Add imports at the top
        if self.imports_to_add:
            converted_lines = self._add_imports(converted_lines)

        return '\n'.join(converted_lines)

    def _convert_assertions(self, line: str) -> str:
        """Convert basic assertions."""
        for pattern, replacement in self.ASSERTION_MAPPINGS.items():
            line = re.sub(pattern, replacement, line)
        return line

    def _convert_assert_raises(self, line: str) -> str:
        """Convert assertRaises patterns."""
        # Simple assertRaises
        line = re.sub(
            r'with self\.assertRaises\(([^)]+)\):',
            r'with pytest.raises(\1):',
            line
        )

        # assertRaisesRegex
        line = re.sub(
            r'self\.assertRaisesRegex\(([^,]+),\s*([^,]+),\s*([^)]+)\)',
            r'with pytest.raises(\1, match=\2): \3',
            line
        )

        return line

    def _convert_assert_almost_equal(self, line: str) -> str:
        """Convert assertAlmostEqual to pytest.approx."""
        # With delta
        line = re.sub(
            r'self\.assertAlmostEqual\(([^,]+),\s*([^,]+),\s*delta=([^)]+)\)',
            r'assert \1 == pytest.approx(\2, abs=\3)',
            line
        )

        # With places
        line = re.sub(
            r'self\.assertAlmostEqual\(([^,]+),\s*([^,]+),\s*places=(\d+)\)',
            lambda m: f'assert {m.group(1)} == pytest.approx({m.group(2)}, abs=1e-{m.group(3)})',
            line
        )

        # Simple (default to abs=1e-7)
        line = re.sub(
            r'self\.assertAlmostEqual\(([^,]+),\s*([^)]+)\)',
            r'assert \1 == pytest.approx(\2, abs=1e-7)',
            line
        )

        return line

    def _convert_setup_to_fixture(self, line_index: int) -> str:
        """Convert setUp method to pytest fixture."""
        # This is a placeholder - setUp conversion needs manual review
        # as it depends on what's being set up
        return "    # TODO: Convert setUp to pytest fixture(s)"

    def _convert_teardown_to_fixture(self, line_index: int) -> str:
        """Convert tearDown method to fixture cleanup."""
        return "    # TODO: Convert tearDown to fixture cleanup"

    def _add_imports(self, lines: List[str]) -> List[str]:
        """Add necessary imports at the top of the file."""
        import_lines = []
        other_lines = []
        docstring_lines = []

        in_docstring = False
        docstring_start = -1

        for i, line in enumerate(lines):
            if line.strip().startswith('"""') and not in_docstring:
                in_docstring = True
                docstring_start = i
                docstring_lines.append(line)
            elif line.strip().endswith('"""') and in_docstring and i != docstring_start:
                in_docstring = False
                docstring_lines.append(line)
            elif in_docstring:
                docstring_lines.append(line)
            elif line.startswith('import ') or line.startswith('from '):
                import_lines.append(line)
            elif line.strip() == '':
                if not import_lines and not other_lines:
                    docstring_lines.append(line)
                else:
                    import_lines.append(line)
            else:
                other_lines.append(line)

        # Reconstruct with new imports
        result = docstring_lines.copy()
        if docstring_lines and import_lines:
            result.append('')

        # Add existing imports
        result.extend(import_lines)

        # Add new imports
        for new_import in sorted(self.imports_to_add):
            if new_import not in [line.strip() for line in import_lines]:
                result.append(new_import)

        # Add a blank line before the rest
        if import_lines or self.imports_to_add:
            result.append('')

        result.extend(other_lines)
        return result

    def save_converted(self, output_path: Path = None) -> Path:
        """Save the converted content to a file."""
        if output_path is None:
            output_path = self.file_path.with_suffix('.pytest.py')

        converted_content = self.convert()
        output_path.write_text(converted_content, encoding='utf-8')
        print(f"Converted file saved to: {output_path}")
        return output_path


def main():
    """Main function to run the converter."""
    if len(sys.argv) != 2:
        print("Usage: python unittest_to_pytest.py <file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File {file_path} does not exist")
        sys.exit(1)

    converter = UnittestToPytestConverter(file_path)
    output_path = converter.save_converted()

    print(f"""
Conversion complete!

Next steps:
1. Review the converted file: {output_path}
2. Handle TODO comments for setUp/tearDown conversion
3. Run tests to ensure functionality: pytest {output_path}
4. Run type checking: mypy {output_path}
5. Run linting: pylint {output_path}

After validation, replace the original file.
    """)


if __name__ == '__main__':
    main()
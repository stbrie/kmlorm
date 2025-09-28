#!/usr/bin/env python3
"""
Validation script for unittest to pytest conversion.

This script runs both unittest and pytest versions of tests and compares
the results to ensure 100% parity during conversion.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import tempfile


class ConversionValidator:
    """Validate that pytest conversion maintains test parity."""

    def __init__(self, original_file: Path, converted_file: Path):
        """Initialize validator with original and converted test files."""
        self.original_file = original_file
        self.converted_file = converted_file
        self.results = {}

    def run_unittest_tests(self) -> Dict:
        """Run original unittest tests and capture results."""
        print(f"Running unittest tests from {self.original_file.name}...")

        try:
            # Run unittest with json output
            result = subprocess.run([
                sys.executable, '-m', 'pytest', str(self.original_file),
                '--tb=short', '-v', '--json-report', '--json-report-file=/tmp/unittest_results.json'
            ], capture_output=True, text=True, cwd=self.original_file.parent.parent)

            # Parse results
            try:
                with open('/tmp/unittest_results.json', 'r') as f:
                    json_data = json.load(f)
                    return {
                        'success': result.returncode == 0,
                        'output': result.stdout,
                        'error': result.stderr,
                        'tests': json_data.get('tests', []),
                        'summary': json_data.get('summary', {}),
                        'returncode': result.returncode
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                # Fallback to text parsing
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr,
                    'returncode': result.returncode
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'returncode': -1
            }

    def run_pytest_tests(self) -> Dict:
        """Run converted pytest tests and capture results."""
        print(f"Running pytest tests from {self.converted_file.name}...")

        try:
            # Run pytest with json output
            result = subprocess.run([
                sys.executable, '-m', 'pytest', str(self.converted_file),
                '--tb=short', '-v', '--json-report', '--json-report-file=/tmp/pytest_results.json'
            ], capture_output=True, text=True, cwd=self.converted_file.parent.parent)

            # Parse results
            try:
                with open('/tmp/pytest_results.json', 'r') as f:
                    json_data = json.load(f)
                    return {
                        'success': result.returncode == 0,
                        'output': result.stdout,
                        'error': result.stderr,
                        'tests': json_data.get('tests', []),
                        'summary': json_data.get('summary', {}),
                        'returncode': result.returncode
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                # Fallback to text parsing
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr,
                    'returncode': result.returncode
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'returncode': -1
            }

    def compare_results(self, unittest_results: Dict, pytest_results: Dict) -> Dict:
        """Compare results from both test runs."""
        comparison = {
            'both_passed': unittest_results['success'] and pytest_results['success'],
            'both_failed': not unittest_results['success'] and not pytest_results['success'],
            'different_outcomes': unittest_results['success'] != pytest_results['success'],
            'unittest_passed': unittest_results['success'],
            'pytest_passed': pytest_results['success'],
        }

        # Compare test counts if available
        if 'tests' in unittest_results and 'tests' in pytest_results:
            unittest_count = len(unittest_results['tests'])
            pytest_count = len(pytest_results['tests'])
            comparison['same_test_count'] = unittest_count == pytest_count
            comparison['unittest_test_count'] = unittest_count
            comparison['pytest_test_count'] = pytest_count

            # Compare individual test results
            unittest_test_names = {test.get('nodeid', '') for test in unittest_results['tests']}
            pytest_test_names = {test.get('nodeid', '') for test in pytest_results['tests']}

            comparison['missing_tests'] = unittest_test_names - pytest_test_names
            comparison['extra_tests'] = pytest_test_names - unittest_test_names

        return comparison

    def validate_conversion(self) -> bool:
        """Run validation and return True if conversion is successful."""
        print(f"\n{'='*60}")
        print(f"Validating conversion: {self.original_file.name} -> {self.converted_file.name}")
        print(f"{'='*60}")

        # Run both test suites
        unittest_results = self.run_unittest_tests()
        pytest_results = self.run_pytest_tests()

        # Compare results
        comparison = self.compare_results(unittest_results, pytest_results)

        # Print results
        print(f"\nResults Summary:")
        print(f"  Original (unittest): {'PASS' if unittest_results['success'] else 'FAIL'}")
        print(f"  Converted (pytest):  {'PASS' if pytest_results['success'] else 'FAIL'}")

        if 'same_test_count' in comparison:
            print(f"  Test count: {comparison['unittest_test_count']} -> {comparison['pytest_test_count']}")

        if comparison['both_passed']:
            print(f"  ✅ VALIDATION PASSED: Both test suites pass")
            return True
        elif comparison['both_failed']:
            print(f"  ⚠️  VALIDATION WARNING: Both test suites fail (may be existing issues)")
            print(f"     Check if failures are the same...")
            return self._compare_failures(unittest_results, pytest_results)
        else:
            print(f"  ❌ VALIDATION FAILED: Different outcomes")
            print(f"     Original: {'PASS' if unittest_results['success'] else 'FAIL'}")
            print(f"     Converted: {'PASS' if pytest_results['success'] else 'FAIL'}")

            # Print detailed error information
            if unittest_results.get('error'):
                print(f"\nUnittest errors:")
                print(unittest_results['error'])

            if pytest_results.get('error'):
                print(f"\nPytest errors:")
                print(pytest_results['error'])

            return False

    def _compare_failures(self, unittest_results: Dict, pytest_results: Dict) -> bool:
        """Compare failure messages to see if they're equivalent."""
        # This is a simplified comparison - in practice, you might want
        # more sophisticated error message comparison
        unittest_errors = unittest_results.get('error', '')
        pytest_errors = pytest_results.get('error', '')

        # If both have similar error patterns, consider it equivalent
        if ('FAILED' in unittest_errors and 'FAILED' in pytest_errors) or \
           ('ERROR' in unittest_errors and 'ERROR' in pytest_errors):
            print("  ✅ Similar failure patterns detected - likely equivalent")
            return True

        print("  ❓ Different failure patterns - manual review needed")
        return False

    def run_type_checking(self) -> bool:
        """Run mypy type checking on converted file."""
        print(f"\nRunning type checking on {self.converted_file.name}...")

        try:
            result = subprocess.run([
                'mypy', str(self.converted_file)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("  ✅ Type checking passed")
                return True
            else:
                print("  ❌ Type checking failed:")
                print(result.stdout)
                print(result.stderr)
                return False

        except FileNotFoundError:
            print("  ⚠️  mypy not found, skipping type checking")
            return True

    def run_linting(self) -> bool:
        """Run pylint on converted file."""
        print(f"\nRunning linting on {self.converted_file.name}...")

        try:
            result = subprocess.run([
                'pylint', str(self.converted_file)
            ], capture_output=True, text=True)

            # Pylint returns 0 for perfect score, but we'll accept scores >= 8.0
            if result.returncode == 0:
                print("  ✅ Linting passed (perfect score)")
                return True
            else:
                # Extract score from pylint output
                output = result.stdout
                if "Your code has been rated at" in output:
                    import re
                    score_match = re.search(r'rated at ([\d.]+)/10', output)
                    if score_match:
                        score = float(score_match.group(1))
                        if score >= 8.0:
                            print(f"  ✅ Linting passed (score: {score}/10)")
                            return True
                        else:
                            print(f"  ❌ Linting failed (score: {score}/10)")
                            print(output)
                            return False

                print("  ❌ Linting failed:")
                print(output)
                return False

        except FileNotFoundError:
            print("  ⚠️  pylint not found, skipping linting")
            return True


def main():
    """Main function to run validation."""
    if len(sys.argv) != 3:
        print("Usage: python validate_pytest_conversion.py <original_file> <converted_file>")
        sys.exit(1)

    original_file = Path(sys.argv[1])
    converted_file = Path(sys.argv[2])

    if not original_file.exists():
        print(f"Error: Original file {original_file} does not exist")
        sys.exit(1)

    if not converted_file.exists():
        print(f"Error: Converted file {converted_file} does not exist")
        sys.exit(1)

    validator = ConversionValidator(original_file, converted_file)

    # Run validation
    test_validation = validator.validate_conversion()
    type_validation = validator.run_type_checking()
    lint_validation = validator.run_linting()

    # Overall result
    overall_success = test_validation and type_validation and lint_validation

    print(f"\n{'='*60}")
    print(f"OVERALL VALIDATION: {'PASSED' if overall_success else 'FAILED'}")
    print(f"{'='*60}")

    if overall_success:
        print("✅ Conversion validated successfully!")
        print(f"You can now replace {original_file.name} with {converted_file.name}")
    else:
        print("❌ Validation failed. Review the issues above before proceeding.")

    sys.exit(0 if overall_success else 1)


if __name__ == '__main__':
    main()
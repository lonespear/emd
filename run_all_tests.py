"""
run_all_tests.py
----------------

Master test suite runner for the EMD soldier qualification system.

Runs all individual test files and generates a comprehensive test report.

Usage:
    python run_all_tests.py              # Run all tests
    python run_all_tests.py --quick      # Run only fast tests
    python run_all_tests.py --report     # Generate detailed report
"""

import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print colored header."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

def print_test_start(test_name):
    """Print test start message."""
    print(f"{Colors.BOLD}{Colors.OKBLUE}[RUNNING]{Colors.ENDC} {test_name}...")

def print_test_result(test_name, passed, duration, details=""):
    """Print test result."""
    if passed:
        status = f"{Colors.OKGREEN}[PASS]{Colors.ENDC}"
    else:
        status = f"{Colors.FAIL}[FAIL]{Colors.ENDC}"

    print(f"{status} {test_name} ({duration:.2f}s)")
    if details:
        print(f"       {details}")

def run_test_file(test_file, timeout=300):
    """
    Run a single test file and return results.

    Returns:
        tuple: (passed, duration, output)
    """
    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )

        duration = time.time() - start_time

        # Check if test passed by looking for SUCCESS in output
        output = result.stdout + result.stderr
        passed = (result.returncode == 0 and
                 ("[SUCCESS]" in output or "All tests passed" in output))

        return passed, duration, output

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return False, duration, f"Test timed out after {timeout}s"
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Test failed with error: {e}"

def extract_test_stats(output):
    """
    Extract test statistics from output.

    Returns:
        dict with test counts
    """
    stats = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }

    # Count [PASS] and [FAIL] markers
    stats['passed'] = output.count('[PASS]')
    stats['failed'] = output.count('[FAIL]')
    stats['warnings'] = output.count('[WARNING]') + output.count('Warning:')
    stats['total'] = stats['passed'] + stats['failed']

    return stats

def main():
    """Run all tests and generate report."""
    import argparse

    parser = argparse.ArgumentParser(description='Run EMD qualification system test suite')
    parser.add_argument('--quick', action='store_true', help='Run only fast tests')
    parser.add_argument('--report', action='store_true', help='Generate detailed report file')
    parser.add_argument('--verbose', action='store_true', help='Show full test output')
    args = parser.parse_args()

    print_header("EMD QUALIFICATION SYSTEM - MASTER TEST SUITE")

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Working directory: {Path.cwd()}")
    print()

    # Define all test files
    all_tests = [
        # Phase 2: Extended profiles
        {
            'name': 'Profile Utilities',
            'file': 'test_profile_utils.py',
            'phase': 2,
            'critical': True,
            'fast': True
        },

        # Phase 3: Billet requirements
        {
            'name': 'Billet Requirements System',
            'file': 'test_billet_requirements.py',
            'phase': 3,
            'critical': True,
            'fast': True
        },

        # Phase 4: Qualification penalties
        {
            'name': 'Qualification Penalties in EMD',
            'file': 'test_qualification_penalties.py',
            'phase': 4,
            'critical': True,
            'fast': False
        },

        # Phase 5: Filtering
        {
            'name': 'Qualification Filter System',
            'file': 'test_qualification_filter.py',
            'phase': 5,
            'critical': True,
            'fast': True
        },

        # Phase 7: Integration
        {
            'name': 'Comprehensive Integration Test',
            'file': 'test_integration.py',
            'phase': 7,
            'critical': True,
            'fast': False
        }
    ]

    # Filter tests if --quick
    if args.quick:
        tests_to_run = [t for t in all_tests if t['fast']]
        print(f"{Colors.WARNING}[QUICK MODE] Running {len(tests_to_run)}/{len(all_tests)} fast tests{Colors.ENDC}\n")
    else:
        tests_to_run = all_tests
        print(f"Running {len(tests_to_run)} test suites\n")

    # Run all tests
    results = []
    total_duration = 0

    for test in tests_to_run:
        test_file = Path(__file__).parent / test['file']

        # Check if file exists
        if not test_file.exists():
            print_test_result(test['name'], False, 0, f"File not found: {test['file']}")
            results.append({
                **test,
                'passed': False,
                'duration': 0,
                'stats': {'total': 0, 'passed': 0, 'failed': 1, 'warnings': 0},
                'output': 'File not found'
            })
            continue

        print_test_start(test['name'])

        # Run test
        passed, duration, output = run_test_file(str(test_file))
        total_duration += duration

        # Extract stats
        stats = extract_test_stats(output)

        # Print result
        details = f"{stats['passed']} passed, {stats['failed']} failed"
        if stats['warnings'] > 0:
            details += f", {stats['warnings']} warnings"

        print_test_result(test['name'], passed, duration, details)

        # Show verbose output if requested
        if args.verbose and not passed:
            print(f"\n{Colors.WARNING}--- Test Output ---{Colors.ENDC}")
            print(output[:2000])  # First 2000 chars
            print(f"{Colors.WARNING}--- End Output ---{Colors.ENDC}\n")

        # Store results
        results.append({
            **test,
            'passed': passed,
            'duration': duration,
            'stats': stats,
            'output': output
        })

    # Print summary
    print_header("TEST SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['passed'])
    failed_tests = total_tests - passed_tests

    total_assertions = sum(r['stats']['passed'] + r['stats']['failed'] for r in results)
    passed_assertions = sum(r['stats']['passed'] for r in results)
    failed_assertions = sum(r['stats']['failed'] for r in results)
    total_warnings = sum(r['stats']['warnings'] for r in results)

    # Overall status
    if failed_tests == 0:
        overall_status = f"{Colors.OKGREEN}ALL TESTS PASSED{Colors.ENDC}"
    elif failed_tests == total_tests:
        overall_status = f"{Colors.FAIL}ALL TESTS FAILED{Colors.ENDC}"
    else:
        overall_status = f"{Colors.WARNING}SOME TESTS FAILED{Colors.ENDC}"

    print(f"Overall Status: {overall_status}")
    print()
    print(f"Test Suites:   {passed_tests}/{total_tests} passed")
    print(f"Assertions:    {passed_assertions}/{total_assertions} passed")
    print(f"Warnings:      {total_warnings}")
    print(f"Total Time:    {total_duration:.2f}s")
    print()

    # Show failures
    if failed_tests > 0:
        print(f"{Colors.FAIL}Failed Test Suites:{Colors.ENDC}")
        for r in results:
            if not r['passed']:
                print(f"  - {r['name']} ({r['file']})")
        print()

    # Critical failures
    critical_failures = [r for r in results if not r['passed'] and r.get('critical', False)]
    if critical_failures:
        print(f"{Colors.FAIL}{Colors.BOLD}CRITICAL FAILURES:{Colors.ENDC}")
        print(f"{Colors.FAIL}The following critical tests failed:{Colors.ENDC}")
        for r in critical_failures:
            print(f"  {Colors.FAIL}[X]{Colors.ENDC} Phase {r['phase']}: {r['name']}")
        print()

    # Generate detailed report if requested
    if args.report:
        report_file = Path(__file__).parent / "test_report.md"
        generate_report(results, report_file, total_duration)
        print(f"Detailed report saved to: {report_file}")
        print()

    # Exit code
    sys.exit(0 if failed_tests == 0 else 1)

def generate_report(results, output_file, total_duration):
    """Generate detailed markdown test report."""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# EMD Qualification System - Test Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['passed'])
        failed_tests = total_tests - passed_tests

        total_assertions = sum(r['stats']['passed'] + r['stats']['failed'] for r in results)
        passed_assertions = sum(r['stats']['passed'] for r in results)

        f.write("## Summary\n\n")
        f.write(f"- **Test Suites:** {passed_tests}/{total_tests} passed\n")
        f.write(f"- **Assertions:** {passed_assertions}/{total_assertions} passed\n")
        f.write(f"- **Total Time:** {total_duration:.2f}s\n")
        f.write(f"- **Overall Status:** {'✅ PASS' if failed_tests == 0 else '❌ FAIL'}\n\n")

        # Results by phase
        f.write("## Results by Phase\n\n")

        phases = {}
        for r in results:
            phase = r.get('phase', 0)
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(r)

        for phase in sorted(phases.keys()):
            f.write(f"### Phase {phase}\n\n")
            f.write("| Test Suite | Status | Duration | Assertions | Warnings |\n")
            f.write("|------------|--------|----------|------------|-----------|\n")

            for r in phases[phase]:
                status = "✅ PASS" if r['passed'] else "❌ FAIL"
                assertions = f"{r['stats']['passed']}/{r['stats']['passed'] + r['stats']['failed']}"
                warnings = r['stats']['warnings']

                f.write(f"| {r['name']} | {status} | {r['duration']:.2f}s | {assertions} | {warnings} |\n")

            f.write("\n")

        # Detailed results
        f.write("## Detailed Results\n\n")

        for r in results:
            status_icon = "✅" if r['passed'] else "❌"
            f.write(f"### {status_icon} {r['name']}\n\n")
            f.write(f"- **File:** `{r['file']}`\n")
            f.write(f"- **Phase:** {r['phase']}\n")
            f.write(f"- **Duration:** {r['duration']:.2f}s\n")
            f.write(f"- **Assertions:** {r['stats']['passed']} passed, {r['stats']['failed']} failed\n")

            if r['stats']['warnings'] > 0:
                f.write(f"- **Warnings:** {r['stats']['warnings']}\n")

            f.write("\n")

            # Show output for failed tests
            if not r['passed']:
                f.write("**Output:**\n\n")
                f.write("```\n")
                # Show last 1000 chars of output
                output = r['output'][-1000:] if len(r['output']) > 1000 else r['output']
                f.write(output)
                f.write("\n```\n\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        if failed_tests == 0:
            f.write("✅ All tests passed! The qualification system is ready for use.\n\n")
        else:
            f.write("⚠️ Some tests failed. Recommended actions:\n\n")

            for r in results:
                if not r['passed']:
                    f.write(f"- **{r['name']}**: Review test output and fix issues\n")

            if any(r.get('critical', False) and not r['passed'] for r in results):
                f.write("\n⚠️ **Critical tests failed** - system may not function correctly\n")

if __name__ == "__main__":
    main()

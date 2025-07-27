#!/usr/bin/env python3
"""
Comprehensive test runner for giv Python implementation.

This script runs all tests and provides detailed reporting on:
- Test coverage
- Compatibility with Bash implementation  
- Performance metrics
- Integration test results
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(cmd, capture_output=True, **kwargs):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            **kwargs
        )
        duration = time.time() - start_time
        print(f"  Completed in {duration:.2f}s (exit code: {result.returncode})")
        return result, duration
    except Exception as e:
        duration = time.time() - start_time
        print(f"  Failed after {duration:.2f}s: {e}")
        return None, duration


def check_dependencies():
    """Check that all required dependencies are available."""
    print("Checking dependencies...")
    
    required_commands = ['python3', 'git', 'pytest']
    optional_commands = ['bash']  # For compatibility tests
    
    missing_required = []
    missing_optional = []
    
    for cmd in required_commands:
        result, _ = run_command(['which', cmd])
        if not result or result.returncode != 0:
            missing_required.append(cmd)
    
    for cmd in optional_commands:
        result, _ = run_command(['which', cmd])
        if not result or result.returncode != 0:
            missing_optional.append(cmd)
    
    if missing_required:
        print(f"❌ Missing required dependencies: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"⚠️  Missing optional dependencies: {', '.join(missing_optional)}")
        print("   Some compatibility tests may be skipped")
    
    print("✅ Dependencies check passed")
    return True


def run_unit_tests(verbose=False):
    """Run unit tests."""
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    cmd = ['python', '-m', 'pytest', 'tests/']
    
    if verbose:
        cmd.extend(['-v', '-s'])
    
    # Add coverage if available
    try:
        import coverage
        cmd.extend(['--cov=giv_cli', '--cov-report=term-missing'])
    except ImportError:
        print("📝 Coverage not available (install with: pip install coverage pytest-cov)")
    
    result, duration = run_command(cmd)
    
    if result and result.returncode == 0:
        print("✅ Unit tests passed")
        return True, duration
    else:
        print("❌ Unit tests failed")
        if result:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        return False, duration


def run_integration_tests(verbose=False):
    """Run integration tests."""
    print("\n" + "="*60)
    print("RUNNING INTEGRATION TESTS")
    print("="*60)
    
    cmd = ['python', '-m', 'pytest', 'tests/test_cli_integration.py']
    
    if verbose:
        cmd.extend(['-v', '-s'])
    
    result, duration = run_command(cmd)
    
    if result and result.returncode == 0:
        print("✅ Integration tests passed")
        return True, duration
    else:
        print("❌ Integration tests failed")
        if result:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        return False, duration


def run_compatibility_tests(verbose=False):
    """Run compatibility tests with Bash implementation."""
    print("\n" + "="*60)
    print("RUNNING COMPATIBILITY TESTS")
    print("="*60)
    
    # Check if bash implementation is available
    bash_giv_path = Path('../giv/src/giv.sh')
    if not bash_giv_path.exists():
        print("⚠️  Bash implementation not found, skipping compatibility tests")
        print(f"   Expected at: {bash_giv_path.absolute()}")
        return True, 0
    
    cmd = ['python', '-m', 'pytest', 'tests/test_compatibility.py']
    
    if verbose:
        cmd.extend(['-v', '-s'])
    
    result, duration = run_command(cmd)
    
    if result and result.returncode == 0:
        print("✅ Compatibility tests passed")
        return True, duration
    else:
        print("❌ Compatibility tests failed")
        if result:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        return False, duration


def run_specific_tests(test_pattern, verbose=False):
    """Run specific tests matching a pattern."""
    print(f"\n" + "="*60)
    print(f"RUNNING TESTS MATCHING: {test_pattern}")
    print("="*60)
    
    cmd = ['python', '-m', 'pytest', '-k', test_pattern]
    
    if verbose:
        cmd.extend(['-v', '-s'])
    
    result, duration = run_command(cmd)
    
    if result and result.returncode == 0:
        print(f"✅ Tests matching '{test_pattern}' passed")
        return True, duration
    else:
        print(f"❌ Tests matching '{test_pattern}' failed")
        if result:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        return False, duration


def validate_installation():
    """Validate that the Python giv implementation works."""
    print("\n" + "="*60)
    print("VALIDATING INSTALLATION")
    print("="*60)
    
    # Test basic CLI functionality
    tests = [
        (['python', '-m', 'giv_cli', '--version'], "Version check"),
        (['python', '-m', 'giv_cli', '--help'], "Help display"),
        (['python', '-m', 'giv_cli', 'config', '--list'], "Config display"),
    ]
    
    all_passed = True
    total_duration = 0
    
    for cmd, description in tests:
        print(f"\nTesting: {description}")
        result, duration = run_command(cmd)
        total_duration += duration
        
        if result and result.returncode == 0:
            print(f"✅ {description} passed")
        else:
            print(f"❌ {description} failed")
            if result:
                print("STDOUT:", result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
                print("STDERR:", result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr)
            all_passed = False
    
    return all_passed, total_duration


def generate_test_report(results):
    """Generate a comprehensive test report."""
    print("\n" + "="*60)
    print("TEST REPORT SUMMARY")
    print("="*60)
    
    total_duration = sum(duration for _, duration in results.values())
    passed_tests = sum(1 for passed, _ in results.values() if passed)
    total_tests = len(results)
    
    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Total time: {total_duration:.2f}s")
    print()
    
    for test_name, (passed, duration) in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name:<25} ({duration:.2f}s)")
    
    print("\n" + "="*60)
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("The Python implementation is ready for production use.")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("Please review the failures above before proceeding.")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run giv Python implementation tests")
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-u', '--unit-only', action='store_true', help='Run only unit tests')
    parser.add_argument('-i', '--integration-only', action='store_true', help='Run only integration tests')
    parser.add_argument('-c', '--compatibility-only', action='store_true', help='Run only compatibility tests')
    parser.add_argument('-k', '--keyword', help='Run tests matching keyword')
    parser.add_argument('--no-validation', action='store_true', help='Skip installation validation')
    parser.add_argument('--quick', action='store_true', help='Run quick test subset')
    
    args = parser.parse_args()
    
    print("🧪 GIV PYTHON IMPLEMENTATION TEST RUNNER")
    print("="*60)
    
    # Change to the correct directory
    os.chdir(Path(__file__).parent)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    results = {}
    
    # Installation validation (unless skipped)
    if not args.no_validation:
        passed, duration = validate_installation()
        results['Installation Validation'] = (passed, duration)
        
        if not passed and not args.verbose:
            print("❌ Installation validation failed. Use -v for details.")
            return 1
    
    # Run specific test suites based on arguments
    if args.keyword:
        passed, duration = run_specific_tests(args.keyword, args.verbose)
        results[f'Tests matching "{args.keyword}"'] = (passed, duration)
    
    elif args.unit_only:
        passed, duration = run_unit_tests(args.verbose)
        results['Unit Tests'] = (passed, duration)
    
    elif args.integration_only:
        passed, duration = run_integration_tests(args.verbose)
        results['Integration Tests'] = (passed, duration)
    
    elif args.compatibility_only:
        passed, duration = run_compatibility_tests(args.verbose)
        results['Compatibility Tests'] = (passed, duration)
    
    elif args.quick:
        # Quick subset for development
        passed, duration = run_unit_tests(args.verbose)
        results['Unit Tests'] = (passed, duration)
        
        if passed:
            passed, duration = run_integration_tests(args.verbose)
            results['Integration Tests'] = (passed, duration)
    
    else:
        # Full test suite
        passed, duration = run_unit_tests(args.verbose)
        results['Unit Tests'] = (passed, duration)
        
        if passed or args.verbose:
            passed, duration = run_integration_tests(args.verbose)
            results['Integration Tests'] = (passed, duration)
        
        if passed or args.verbose:
            passed, duration = run_compatibility_tests(args.verbose)
            results['Compatibility Tests'] = (passed, duration)
    
    # Generate final report
    all_passed = generate_test_report(results)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())

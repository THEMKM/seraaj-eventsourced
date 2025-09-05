#!/usr/bin/env python3
"""
Contract Compliance Testing CLI Tool
Automated validation of API contracts, schemas, and service implementations
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.contract_validator import contract_validator, ComplianceStatus


def print_detailed_report(results: dict):
    """Print detailed contract compliance report"""
    print("\n" + "="*60)
    print("📋 DETAILED CONTRACT COMPLIANCE REPORT")
    print("="*60)
    
    # Overview
    print(f"\n📊 Overview:")
    print(f"   Contract Version: {results['contract_version']}")
    print(f"   Timestamp: {results['timestamp']}")
    print(f"   Execution Time: {results['execution_time_seconds']:.2f}s")
    print(f"   Overall Status: {results['overall_status'].upper()}")
    
    # Test Summary
    print(f"\n🧪 Test Summary:")
    print(f"   Total Tests: {results['tests_run']}")
    print(f"   ✅ Passed: {results['tests_passed']}")
    print(f"   ❌ Failed: {results['tests_failed']}")
    print(f"   ⚠️ Degraded: {results['tests_degraded']}")
    print(f"   🚫 Errors: {results['tests_errored']}")
    
    # Success rate
    if results['tests_run'] > 0:
        success_rate = (results['tests_passed'] / results['tests_run']) * 100
        print(f"   📈 Success Rate: {success_rate:.1f}%")
    
    # Individual test results
    print(f"\n🔍 Individual Test Results:")
    for test_result in results['results']:
        status = test_result['status']
        status_icons = {
            'compliant': '✅',
            'degraded': '⚠️',
            'non_compliant': '❌',
            'error': '🚫',
            'unknown': '❓'
        }
        icon = status_icons.get(status, '❓')
        
        print(f"\n   {icon} {test_result['test_name'].upper()}")
        print(f"      Status: {status}")
        print(f"      Message: {test_result['message']}")
        print(f"      Execution Time: {test_result['execution_time_ms']:.1f}ms")
        
        if test_result.get('details'):
            print(f"      Details:")
            for key, value in test_result['details'].items():
                print(f"        • {key}: {value}")
        
        if test_result.get('errors'):
            print(f"      Errors:")
            for error in test_result['errors']:
                print(f"        ❌ {error}")
        
        if test_result.get('warnings'):
            print(f"      Warnings:")
            for warning in test_result['warnings']:
                print(f"        ⚠️ {warning}")
    
    # Recommendations
    if results.get('recommendations'):
        print(f"\n💡 Recommendations:")
        for rec in results['recommendations']:
            print(f"   • {rec}")
    
    print(f"\n" + "="*60)


def print_summary_report(results: dict):
    """Print concise summary report"""
    status_emoji = {
        'compliant': '✅',
        'degraded': '⚠️',
        'non_compliant': '❌',
        'error': '🚫',
        'unknown': '❓'
    }
    
    overall_status = results['overall_status']
    emoji = status_emoji.get(overall_status, '❓')
    
    print(f"\n{emoji} Contract Compliance: {overall_status.upper()}")
    print(f"   Tests: {results['tests_passed']}/{results['tests_run']} passed")
    
    if results['tests_failed'] > 0:
        failed_tests = [r for r in results['results'] if r['status'] == 'non_compliant']
        print(f"   Failed tests: {', '.join(r['test_name'] for r in failed_tests)}")
    
    if results.get('recommendations'):
        print(f"   Top recommendation: {results['recommendations'][0]}")


async def run_tests_command(output_format: str = "summary", save_report: bool = False):
    """Run contract compliance tests"""
    print("🔍 Running contract compliance tests...")
    
    try:
        results = await contract_validator.validate_all_contracts()
        
        if output_format == "detailed":
            print_detailed_report(results)
        elif output_format == "json":
            print(json.dumps(results, indent=2))
        else:  # summary
            print_summary_report(results)
        
        # Save report if requested
        if save_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"contract_compliance_report_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Report saved to: {report_file}")
        
        # Return exit code based on compliance status
        if results['overall_status'] == 'compliant':
            return 0
        elif results['overall_status'] in ['degraded', 'unknown']:
            return 1  # Warning level
        else:
            return 2  # Error level
            
    except Exception as e:
        print(f"❌ Error running contract tests: {e}")
        return 3


async def validate_specific_contract(contract_name: str):
    """Validate a specific contract"""
    print(f"🔍 Validating contract: {contract_name}")
    
    # Find matching test
    matching_tests = [test for test in contract_validator.tests if contract_name.lower() in test.name.lower()]
    
    if not matching_tests:
        print(f"❌ No tests found matching: {contract_name}")
        print(f"Available tests: {', '.join(test.name for test in contract_validator.tests)}")
        return 1
    
    # Run only matching tests
    original_tests = contract_validator.tests
    contract_validator.tests = matching_tests
    
    try:
        results = await contract_validator.validate_all_contracts()
        print_summary_report(results)
        
        return 0 if results['overall_status'] == 'compliant' else 1
        
    finally:
        contract_validator.tests = original_tests


async def list_contracts_command():
    """List available contracts and tests"""
    print("\n📋 Available Contract Tests:")
    print("-" * 40)
    
    for test in contract_validator.tests:
        critical_icon = "🔴" if test.critical else "🟡"
        print(f"\n{critical_icon} {test.name}")
        print(f"   Description: {test.description}")
        print(f"   Type: {test.test_type}")
        print(f"   Service: {test.service_url}")
        print(f"   Contract: {test.contract_path}")
        print(f"   Critical: {'Yes' if test.critical else 'No'}")


async def health_check_command():
    """Quick health check for contract compliance"""
    print("🏥 Running quick contract health check...")
    
    # Run just the health compliance test
    health_tests = [test for test in contract_validator.tests if "health" in test.name]
    
    if not health_tests:
        print("❌ No health compliance tests configured")
        return 1
    
    original_tests = contract_validator.tests
    contract_validator.tests = health_tests
    
    try:
        results = await contract_validator.validate_all_contracts()
        
        if results['overall_status'] == 'compliant':
            print("✅ All services healthy and compliant")
            return 0
        else:
            print(f"⚠️ Health check issues: {results['overall_status']}")
            for result in results['results']:
                if result['status'] != 'compliant':
                    print(f"   • {result['test_name']}: {result['message']}")
            return 1
            
    finally:
        contract_validator.tests = original_tests


async def ci_command():
    """Optimized command for CI/CD pipelines"""
    print("🤖 Running contract compliance for CI/CD...")
    
    results = await contract_validator.validate_all_contracts()
    
    # Print CI-friendly output
    status = results['overall_status']
    print(f"CONTRACT_COMPLIANCE_STATUS={status}")
    print(f"TESTS_PASSED={results['tests_passed']}")
    print(f"TESTS_TOTAL={results['tests_run']}")
    
    if status != 'compliant':
        print("CONTRACT_COMPLIANCE_FAILURES:")
        failed_tests = [r for r in results['results'] if r['status'] in ['non_compliant', 'error']]
        for test in failed_tests:
            print(f"  - {test['test_name']}: {test['message']}")
    
    # Set exit code for CI
    if status == 'compliant':
        return 0
    elif status == 'degraded':
        return 1
    else:
        return 2


async def main():
    parser = argparse.ArgumentParser(
        description="Contract Compliance Testing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all contract tests with summary output
  python scripts/contract_tests.py test

  # Run tests with detailed report
  python scripts/contract_tests.py test --format detailed

  # Save report to file
  python scripts/contract_tests.py test --save-report

  # Test specific contract
  python scripts/contract_tests.py validate --contract bff_openapi

  # Quick health check
  python scripts/contract_tests.py health

  # CI/CD optimized run
  python scripts/contract_tests.py ci

  # List available contracts
  python scripts/contract_tests.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run all contract compliance tests')
    test_parser.add_argument('--format', choices=['summary', 'detailed', 'json'], 
                            default='summary', help='Output format')
    test_parser.add_argument('--save-report', action='store_true',
                            help='Save detailed report to file')
    
    # Validate specific contract
    validate_parser = subparsers.add_parser('validate', help='Validate specific contract')
    validate_parser.add_argument('--contract', required=True, 
                                help='Contract name or pattern to validate')
    
    # Health check
    health_parser = subparsers.add_parser('health', help='Quick health check')
    
    # CI command
    ci_parser = subparsers.add_parser('ci', help='CI/CD optimized test run')
    
    # List contracts
    list_parser = subparsers.add_parser('list', help='List available contracts')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'test':
            return await run_tests_command(
                output_format=args.format,
                save_report=args.save_report
            )
        elif args.command == 'validate':
            return await validate_specific_contract(args.contract)
        elif args.command == 'health':
            return await health_check_command()
        elif args.command == 'ci':
            return await ci_command()
        elif args.command == 'list':
            await list_contracts_command()
            return 0
            
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
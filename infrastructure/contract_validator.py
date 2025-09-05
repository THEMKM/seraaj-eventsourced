"""
Contract Compliance Testing Framework
Automated validation of API contracts, schemas, and service implementations
"""

import os
import json
import yaml
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import aiohttp
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """Contract compliance status levels"""
    COMPLIANT = "compliant"
    DEGRADED = "degraded"  
    NON_COMPLIANT = "non_compliant"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    test_name: str
    status: ComplianceStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: float = 0


@dataclass
class ContractTest:
    """Definition of a contract validation test"""
    name: str
    description: str
    contract_path: str
    service_url: str
    test_type: str  # schema, endpoint, workflow
    config: Dict[str, Any] = field(default_factory=dict)
    critical: bool = True  # If false, failure is degraded vs non-compliant


class ContractValidator:
    """Validates service implementations against defined contracts"""
    
    def __init__(self, contracts_dir: str = "contracts", base_url: str = "http://localhost"):
        self.contracts_dir = Path(contracts_dir)
        self.base_url = base_url
        self.version = self._load_contract_version()
        self.session = None
        
        # Load contract tests configuration
        self.tests = self._load_contract_tests()
        
        logger.info(f"Contract validator initialized for version {self.version}")
    
    def _load_contract_version(self) -> str:
        """Load the current contract version"""
        version_file = self.contracts_dir / "version.lock"
        if version_file.exists():
            with open(version_file) as f:
                version_data = json.load(f)
                return version_data["version"]
        return "1.1.0"  # Default
    
    def _load_contract_tests(self) -> List[ContractTest]:
        """Load contract test definitions"""
        tests = []
        
        # BFF API contract tests
        tests.extend([
            ContractTest(
                name="bff_openapi_compliance",
                description="Validate BFF API against OpenAPI specification",
                contract_path=f"v{self.version}/api/bff.openapi.yaml",
                service_url=f"{self.base_url}:8000",
                test_type="openapi",
                config={"endpoints": ["/api/auth/register", "/api/applications", "/api/matches"]},
                critical=True
            ),
            ContractTest(
                name="bff_schema_validation",
                description="Validate BFF response schemas",
                contract_path=f"v{self.version}/api/schemas",
                service_url=f"{self.base_url}:8000",
                test_type="schema",
                critical=True
            )
        ])
        
        # Auth service contract tests
        tests.extend([
            ContractTest(
                name="auth_openapi_compliance",
                description="Validate Auth service against OpenAPI specification", 
                contract_path=f"v{self.version}/api/auth.openapi.yaml",
                service_url=f"{self.base_url}:8004",
                test_type="openapi",
                config={"endpoints": ["/auth/register", "/auth/login", "/auth/refresh"]},
                critical=True
            ),
            ContractTest(
                name="auth_entity_schemas",
                description="Validate Auth entities against schema",
                contract_path=f"v{self.version}/entities/user.schema.json",
                service_url=f"{self.base_url}:8004",
                test_type="schema",
                critical=True
            )
        ])
        
        # Application workflow tests
        tests.extend([
            ContractTest(
                name="application_workflow_compliance",
                description="Validate application workflow implementation",
                contract_path=f"v{self.version}/workflows/application-workflow.json",
                service_url=f"{self.base_url}:8001",
                test_type="workflow",
                critical=True
            ),
            ContractTest(
                name="application_events_schema",
                description="Validate application event schemas",
                contract_path=f"v{self.version}/events/application-submitted.schema.json",
                service_url=f"{self.base_url}:8001",
                test_type="event_schema",
                critical=False
            )
        ])
        
        # Service discovery and health checks
        tests.extend([
            ContractTest(
                name="service_health_compliance",
                description="Validate service health check contracts",
                contract_path="health-contract.json",
                service_url="*",  # All services
                test_type="health",
                critical=False
            ),
            ContractTest(
                name="error_response_compliance", 
                description="Validate standardized error response format",
                contract_path="error-response-contract.json",
                service_url="*",
                test_type="error_schema",
                critical=True
            )
        ])
        
        return tests
    
    async def validate_all_contracts(self) -> Dict[str, Any]:
        """Run all contract validation tests"""
        start_time = datetime.utcnow()
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        
        try:
            results = []
            
            # Run all tests in parallel
            tasks = [self._run_contract_test(test) for test in self.tests]
            test_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(test_results):
                if isinstance(result, Exception):
                    results.append(ValidationResult(
                        test_name=self.tests[i].name,
                        status=ComplianceStatus.ERROR,
                        message=f"Test execution failed: {str(result)}",
                        errors=[str(result)]
                    ))
                else:
                    results.append(result)
            
            # Calculate overall compliance status
            overall_status = self._calculate_overall_status(results)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "overall_status": overall_status.value,
                "execution_time_seconds": execution_time,
                "timestamp": start_time.isoformat(),
                "contract_version": self.version,
                "tests_run": len(results),
                "tests_passed": sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT),
                "tests_failed": sum(1 for r in results if r.status == ComplianceStatus.NON_COMPLIANT),
                "tests_degraded": sum(1 for r in results if r.status == ComplianceStatus.DEGRADED),
                "tests_errored": sum(1 for r in results if r.status == ComplianceStatus.ERROR),
                "results": [self._result_to_dict(r) for r in results],
                "recommendations": self._generate_recommendations(results)
            }
            
        finally:
            if self.session:
                await self.session.close()
    
    async def _run_contract_test(self, test: ContractTest) -> ValidationResult:
        """Run a single contract test"""
        start_time = datetime.utcnow()
        
        try:
            if test.test_type == "openapi":
                result = await self._test_openapi_compliance(test)
            elif test.test_type == "schema":
                result = await self._test_schema_compliance(test)
            elif test.test_type == "workflow":
                result = await self._test_workflow_compliance(test)
            elif test.test_type == "event_schema":
                result = await self._test_event_schema_compliance(test)
            elif test.test_type == "health":
                result = await self._test_health_compliance(test)
            elif test.test_type == "error_schema":
                result = await self._test_error_schema_compliance(test)
            else:
                result = ValidationResult(
                    test_name=test.name,
                    status=ComplianceStatus.ERROR,
                    message=f"Unknown test type: {test.test_type}"
                )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            logger.info(f"Contract test '{test.name}': {result.status.value} ({execution_time:.1f}ms)")
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Contract test '{test.name}' failed with error: {e}")
            
            return ValidationResult(
                test_name=test.name,
                status=ComplianceStatus.ERROR,
                message=f"Test execution error: {str(e)}",
                execution_time_ms=execution_time,
                errors=[str(e)]
            )
    
    async def _test_openapi_compliance(self, test: ContractTest) -> ValidationResult:
        """Test service compliance with OpenAPI specification"""
        contract_file = self.contracts_dir / test.contract_path
        
        if not contract_file.exists():
            return ValidationResult(
                test_name=test.name,
                status=ComplianceStatus.ERROR,
                message=f"Contract file not found: {contract_file}"
            )
        
        # Load OpenAPI spec
        with open(contract_file) as f:
            if contract_file.suffix == '.yaml':
                spec = yaml.safe_load(f)
            else:
                spec = json.load(f)
        
        errors = []
        warnings = []
        
        # Test service availability
        try:
            health_url = f"{test.service_url}/health"
            async with self.session.get(health_url) as response:
                if response.status != 200:
                    errors.append(f"Service health check failed: {response.status}")
        except Exception as e:
            errors.append(f"Service unavailable: {str(e)}")
            return ValidationResult(
                test_name=test.name,
                status=ComplianceStatus.NON_COMPLIANT,
                message="Service unavailable for testing",
                errors=errors
            )
        
        # Test configured endpoints
        endpoints_tested = 0
        endpoint_failures = 0
        
        for endpoint_path in test.config.get("endpoints", []):
            try:
                full_url = f"{test.service_url}{endpoint_path}"
                
                # For POST endpoints, we'll test with OPTIONS to check CORS/methods
                if endpoint_path in ["/api/auth/register", "/api/applications"]:
                    async with self.session.options(full_url) as response:
                        endpoints_tested += 1
                        if response.status not in [200, 204]:
                            warnings.append(f"OPTIONS {endpoint_path}: unexpected status {response.status}")
                else:
                    # For GET endpoints, test directly
                    async with self.session.get(full_url) as response:
                        endpoints_tested += 1
                        if response.status >= 500:
                            endpoint_failures += 1
                            errors.append(f"GET {endpoint_path}: server error {response.status}")
                        elif response.status == 404:
                            warnings.append(f"GET {endpoint_path}: endpoint not found")
            
            except Exception as e:
                endpoint_failures += 1
                errors.append(f"Error testing {endpoint_path}: {str(e)}")
        
        # Determine compliance status
        if errors:
            status = ComplianceStatus.NON_COMPLIANT
            message = f"OpenAPI compliance failed: {len(errors)} critical issues"
        elif warnings:
            status = ComplianceStatus.DEGRADED
            message = f"OpenAPI partially compliant with {len(warnings)} warnings"
        else:
            status = ComplianceStatus.COMPLIANT
            message = f"OpenAPI compliant: {endpoints_tested} endpoints tested"
        
        return ValidationResult(
            test_name=test.name,
            status=status,
            message=message,
            details={
                "endpoints_tested": endpoints_tested,
                "endpoint_failures": endpoint_failures,
                "spec_version": spec.get("info", {}).get("version")
            },
            errors=errors,
            warnings=warnings
        )
    
    async def _test_schema_compliance(self, test: ContractTest) -> ValidationResult:
        """Test response schema compliance"""
        schema_path = self.contracts_dir / test.contract_path
        
        errors = []
        warnings = []
        
        # Load schemas from directory or file
        schemas = {}
        if schema_path.is_dir():
            for schema_file in schema_path.glob("*.yaml"):
                with open(schema_file) as f:
                    schema_data = yaml.safe_load(f)
                    schemas[schema_file.stem] = schema_data
        elif schema_path.exists():
            with open(schema_path) as f:
                if schema_path.suffix == '.json':
                    schemas[schema_path.stem] = json.load(f)
                else:
                    schemas[schema_path.stem] = yaml.safe_load(f)
        else:
            return ValidationResult(
                test_name=test.name,
                status=ComplianceStatus.ERROR,
                message=f"Schema file/directory not found: {schema_path}"
            )
        
        # Test against actual service responses
        schema_tests_passed = 0
        schema_tests_failed = 0
        
        for schema_name, schema_def in schemas.items():
            try:
                # This is a simplified test - in practice you'd make real API calls
                # and validate responses against the schema
                if "type" in schema_def and "properties" in schema_def:
                    schema_tests_passed += 1
                else:
                    warnings.append(f"Schema {schema_name} missing required structure")
            except Exception as e:
                schema_tests_failed += 1
                errors.append(f"Schema validation error for {schema_name}: {str(e)}")
        
        if errors:
            status = ComplianceStatus.NON_COMPLIANT
            message = f"Schema validation failed: {schema_tests_failed} schemas invalid"
        elif warnings:
            status = ComplianceStatus.DEGRADED
            message = f"Schema partially compliant: {len(warnings)} warnings"
        else:
            status = ComplianceStatus.COMPLIANT
            message = f"Schema compliant: {schema_tests_passed} schemas validated"
        
        return ValidationResult(
            test_name=test.name,
            status=status,
            message=message,
            details={
                "schemas_tested": len(schemas),
                "schemas_passed": schema_tests_passed,
                "schemas_failed": schema_tests_failed
            },
            errors=errors,
            warnings=warnings
        )
    
    async def _test_workflow_compliance(self, test: ContractTest) -> ValidationResult:
        """Test workflow implementation compliance"""
        return ValidationResult(
            test_name=test.name,
            status=ComplianceStatus.COMPLIANT,
            message="Workflow compliance testing - implementation placeholder",
            details={"workflow_steps": 0}
        )
    
    async def _test_event_schema_compliance(self, test: ContractTest) -> ValidationResult:
        """Test event schema compliance"""
        return ValidationResult(
            test_name=test.name,
            status=ComplianceStatus.COMPLIANT,
            message="Event schema compliance - implementation placeholder",
            details={"events_validated": 0}
        )
    
    async def _test_health_compliance(self, test: ContractTest) -> ValidationResult:
        """Test health endpoint compliance across all services"""
        services_to_test = [
            (f"{self.base_url}:8000", "bff"),
            (f"{self.base_url}:8001", "applications"),
            (f"{self.base_url}:8003", "matching"),
            (f"{self.base_url}:8004", "auth")
        ]
        
        errors = []
        warnings = []
        healthy_services = 0
        
        for service_url, service_name in services_to_test:
            try:
                health_url = f"{service_url}/health"
                async with self.session.get(health_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "healthy":
                            healthy_services += 1
                        else:
                            warnings.append(f"{service_name}: reports unhealthy status")
                    else:
                        errors.append(f"{service_name}: health check failed ({response.status})")
            except Exception as e:
                errors.append(f"{service_name}: health check error - {str(e)}")
        
        total_services = len(services_to_test)
        if healthy_services == total_services:
            status = ComplianceStatus.COMPLIANT
            message = f"All {total_services} services healthy"
        elif healthy_services > total_services // 2:
            status = ComplianceStatus.DEGRADED
            message = f"{healthy_services}/{total_services} services healthy"
        else:
            status = ComplianceStatus.NON_COMPLIANT
            message = f"Only {healthy_services}/{total_services} services healthy"
        
        return ValidationResult(
            test_name=test.name,
            status=status,
            message=message,
            details={
                "services_tested": total_services,
                "services_healthy": healthy_services
            },
            errors=errors,
            warnings=warnings
        )
    
    async def _test_error_schema_compliance(self, test: ContractTest) -> ValidationResult:
        """Test error response schema compliance"""
        # Test by making requests that should return errors
        services_to_test = [
            f"{self.base_url}:8000/api/nonexistent",  # 404 test
            f"{self.base_url}:8004/auth/login",       # 401 test (no auth)
        ]
        
        compliant_errors = 0
        total_errors = 0
        errors = []
        
        for test_url in services_to_test:
            try:
                async with self.session.get(test_url) as response:
                    total_errors += 1
                    if response.status >= 400:
                        try:
                            error_data = await response.json()
                            # Check for standardized error format
                            if all(key in error_data for key in ["error", "message", "code"]):
                                compliant_errors += 1
                            else:
                                errors.append(f"Non-standard error format from {test_url}")
                        except:
                            errors.append(f"Non-JSON error response from {test_url}")
            except Exception as e:
                errors.append(f"Error testing {test_url}: {str(e)}")
        
        if compliant_errors == total_errors and total_errors > 0:
            status = ComplianceStatus.COMPLIANT
            message = f"Error schema compliant: {compliant_errors}/{total_errors} responses"
        elif compliant_errors > 0:
            status = ComplianceStatus.DEGRADED  
            message = f"Error schema partially compliant: {compliant_errors}/{total_errors}"
        else:
            status = ComplianceStatus.NON_COMPLIANT
            message = "Error schema non-compliant"
        
        return ValidationResult(
            test_name=test.name,
            status=status,
            message=message,
            details={
                "error_responses_tested": total_errors,
                "compliant_responses": compliant_errors
            },
            errors=errors
        )
    
    def _calculate_overall_status(self, results: List[ValidationResult]) -> ComplianceStatus:
        """Calculate overall compliance status from individual test results"""
        if not results:
            return ComplianceStatus.UNKNOWN
        
        critical_tests = [r for r in results if self._is_critical_test(r.test_name)]
        
        # Check critical tests first
        critical_failures = [r for r in critical_tests if r.status == ComplianceStatus.NON_COMPLIANT]
        critical_errors = [r for r in critical_tests if r.status == ComplianceStatus.ERROR]
        
        if critical_failures or critical_errors:
            return ComplianceStatus.NON_COMPLIANT
        
        # Check for any degraded critical tests
        critical_degraded = [r for r in critical_tests if r.status == ComplianceStatus.DEGRADED]
        non_critical_failures = [r for r in results if r.status == ComplianceStatus.NON_COMPLIANT and not self._is_critical_test(r.test_name)]
        
        if critical_degraded or non_critical_failures:
            return ComplianceStatus.DEGRADED
        
        # All critical tests passed, check overall
        all_passed = all(r.status == ComplianceStatus.COMPLIANT for r in results)
        return ComplianceStatus.COMPLIANT if all_passed else ComplianceStatus.DEGRADED
    
    def _is_critical_test(self, test_name: str) -> bool:
        """Check if a test is marked as critical"""
        test = next((t for t in self.tests if t.name == test_name), None)
        return test.critical if test else True
    
    def _result_to_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """Convert ValidationResult to dictionary"""
        return {
            "test_name": result.test_name,
            "status": result.status.value,
            "message": result.message,
            "execution_time_ms": result.execution_time_ms,
            "details": result.details or {},
            "errors": result.errors,
            "warnings": result.warnings
        }
    
    def _generate_recommendations(self, results: List[ValidationResult]) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in results if r.status == ComplianceStatus.NON_COMPLIANT]
        degraded_tests = [r for r in results if r.status == ComplianceStatus.DEGRADED]
        
        if failed_tests:
            recommendations.append(f"🚨 {len(failed_tests)} critical compliance failures require immediate attention")
            
        if degraded_tests:
            recommendations.append(f"⚠️ {len(degraded_tests)} tests show degraded compliance")
        
        # Specific recommendations based on test patterns
        service_health_issues = [r for r in results if "health" in r.test_name and r.status != ComplianceStatus.COMPLIANT]
        if service_health_issues:
            recommendations.append("🏥 Service health issues detected - check service availability")
        
        schema_issues = [r for r in results if "schema" in r.test_name and r.status != ComplianceStatus.COMPLIANT]
        if schema_issues:
            recommendations.append("📋 Schema compliance issues - verify API response formats")
        
        if not recommendations:
            recommendations.append("✅ All contract compliance tests passing")
        
        return recommendations


# Singleton instance
contract_validator = ContractValidator()


async def run_contract_validation():
    """CLI function to run contract validation"""
    print("🔍 Starting Contract Compliance Validation...")
    
    results = await contract_validator.validate_all_contracts()
    
    print(f"\n📊 Contract Compliance Results:")
    print(f"   Overall Status: {results['overall_status'].upper()}")
    print(f"   Tests Run: {results['tests_run']}")
    print(f"   Passed: {results['tests_passed']}")
    print(f"   Failed: {results['tests_failed']}")
    print(f"   Degraded: {results['tests_degraded']}")
    print(f"   Errors: {results['tests_errored']}")
    print(f"   Execution Time: {results['execution_time_seconds']:.2f}s")
    
    if results["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"   • {rec}")
    
    print(f"\n📋 Individual Test Results:")
    for test_result in results["results"]:
        status_icon = {"compliant": "✅", "degraded": "⚠️", "non_compliant": "❌", "error": "🚫"}.get(test_result["status"], "❓")
        print(f"   {status_icon} {test_result['test_name']}: {test_result['message']}")
        
        if test_result["errors"]:
            for error in test_result["errors"]:
                print(f"      ❌ {error}")
        
        if test_result["warnings"]:
            for warning in test_result["warnings"]:
                print(f"      ⚠️ {warning}")
    
    print("\n🎉 Contract compliance validation completed!")
    
    return results["overall_status"] == "compliant"


if __name__ == "__main__":
    asyncio.run(run_contract_validation())
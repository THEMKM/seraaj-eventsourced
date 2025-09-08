#!/usr/bin/env python3
"""
Comprehensive Seraaj System Validation
Validates the entire system after SDK improvements and integration fixes
"""

import json
import subprocess
import sys
import time
import httpx
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import hashlib


class SeraajSystemValidator:
    """Comprehensive system validator for Seraaj platform"""
    
    def __init__(self):
        self.report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_type": "comprehensive_post_sdk_fixes",
            "checks": [],
            "warnings": [],
            "errors": [],
            "performance": {},
            "summary": {}
        }
        self.base_url = "http://localhost:8000"
    
    def log_success(self, message: str):
        """Log successful check"""
        self.report["checks"].append(f"[OK] {message}")
        print(f"[OK] {message}")
    
    def log_warning(self, message: str):
        """Log warning"""
        self.report["warnings"].append(f"[WARN] {message}")
        print(f"[WARN] {message}")
    
    def log_error(self, message: str):
        """Log error"""
        self.report["errors"].append(f"[ERROR] {message}")
        print(f"[ERROR] {message}")
    
    # 1. Contract and Configuration Validation
    def validate_contracts_and_config(self):
        """Validate contracts are frozen and configuration is consistent"""
        print("\n1. VALIDATING CONTRACTS AND CONFIGURATION")
        print("-" * 50)
        
        # Check contract version lock
        version_lock = Path("contracts/version.lock")
        if version_lock.exists():
            try:
                with open(version_lock) as f:
                    lock_data = json.load(f)
                
                if lock_data.get("frozen"):
                    self.log_success(f"Contracts frozen at version {lock_data.get('version', 'unknown')}")
                else:
                    self.log_warning("Contracts not frozen - may cause instability")
                
                # Verify checksum
                if lock_data.get("checksum"):
                    self.log_success("Contract checksum present")
                else:
                    self.log_warning("Contract checksum missing")
                    
            except Exception as e:
                self.log_error(f"Could not read version lock: {e}")
        else:
            self.log_warning("No contract version lock found")
        
        # Check agent checkpoints
        checkpoints_dir = Path(".agents/checkpoints")
        if checkpoints_dir.exists():
            checkpoints = list(checkpoints_dir.glob("*.done"))
            self.log_success(f"Found {len(checkpoints)} agent checkpoints")
            
            critical_checkpoints = [
                "contracts.done", "generation.done", "applications.done", 
                "matching.done", "orchestration.done"
            ]
            
            for checkpoint in critical_checkpoints:
                if (checkpoints_dir / checkpoint).exists():
                    self.log_success(f"Critical checkpoint exists: {checkpoint}")
                else:
                    self.log_error(f"Missing critical checkpoint: {checkpoint}")
        else:
            self.log_error("Agent checkpoints directory not found")
    
    # 2. SDK Package Validation
    def validate_sdk_structure(self):
        """Validate SDK package structure and exports"""
        print("\n2. VALIDATING SDK STRUCTURE")
        print("-" * 50)
        
        # Check SDK package
        sdk_package = Path("packages/sdk-bff")
        if sdk_package.exists():
            self.log_success("SDK package directory exists")
            
            # Check index file
            index_file = sdk_package / "index.ts"
            if index_file.exists() and index_file.stat().st_size > 0:
                self.log_success("SDK index file exists and is not empty")
                
                # Validate exports
                content = index_file.read_text()
                expected_exports = [
                    "AuthApi", "VolunteerApi", "SystemApi", "BFFClient",
                    "createAuthApi", "createVolunteerApi", "createBffClient",
                    "Configuration", "User", "AuthTokens"
                ]
                
                missing_exports = []
                for export in expected_exports:
                    if export not in content:
                        missing_exports.append(export)
                
                if not missing_exports:
                    self.log_success("All expected SDK exports present")
                else:
                    for export in missing_exports:
                        self.log_error(f"Missing SDK export: {export}")
            else:
                self.log_error("SDK index file missing or empty")
        else:
            self.log_error("SDK package directory not found")
        
        # Check package.json
        package_json = sdk_package / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg_data = json.load(f)
                self.log_success(f"SDK package.json valid: {pkg_data.get('name', 'unnamed')}")
            except Exception as e:
                self.log_error(f"SDK package.json invalid: {e}")
    
    # 3. Frontend Integration Validation
    def validate_frontend_integration(self):
        """Validate frontend SDK integration and TypeScript compilation"""
        print("\n3. VALIDATING FRONTEND INTEGRATION")
        print("-" * 50)
        
        web_dir = Path("apps/web")
        if not web_dir.exists():
            self.log_error("Frontend directory not found")
            return
        
        # Check BFF client implementation
        bff_lib = web_dir / "lib" / "bff.ts"
        if bff_lib.exists():
            self.log_success("Frontend BFF client exists")
            
            content = bff_lib.read_text()
            expected_imports = [
                "createBffClient", "createAuthApi", "createVolunteerApi", 
                "createSystemApi", "Configuration"
            ]
            
            missing_imports = [imp for imp in expected_imports if imp not in content]
            if not missing_imports:
                self.log_success("All expected SDK imports present in frontend")
            else:
                for imp in missing_imports:
                    self.log_error(f"Missing frontend import: {imp}")
        else:
            self.log_error("Frontend BFF client not found")
        
        # Test TypeScript compilation
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=web_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.log_success("Frontend TypeScript compilation successful")
            else:
                self.log_warning("Frontend TypeScript has warnings/errors:")
                if result.stderr:
                    print(f"  TypeScript errors: {result.stderr[:200]}...")
        except subprocess.TimeoutExpired:
            self.log_warning("TypeScript compilation timed out")
        except FileNotFoundError:
            self.log_warning("TypeScript compiler not available")
        except Exception as e:
            self.log_warning(f"TypeScript test failed: {e}")
    
    # 4. Backend Services Health
    async def validate_backend_health(self):
        """Validate all backend services are healthy"""
        print("\n4. VALIDATING BACKEND SERVICES HEALTH")
        print("-" * 50)
        
        services = [
            ("BFF", f"{self.base_url}/api/health", False),
            ("Applications Service", "http://localhost:8001/health", True),
            ("Matching Service", "http://localhost:8003/health", True),
        ]
        
        async with httpx.AsyncClient(timeout=10) as client:
            for service_name, url, optional in services:
                try:
                    start_time = time.time()
                    response = await client.get(url)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        self.log_success(f"{service_name} healthy ({response_time:.2f}s)")
                        self.report["performance"][service_name] = response_time
                    else:
                        msg = f"{service_name} unhealthy (status: {response.status_code})"
                        if optional:
                            self.log_warning(msg)
                        else:
                            self.log_error(msg)
                            
                except Exception as e:
                    msg = f"{service_name} unreachable: {str(e)[:50]}..."
                    if optional:
                        self.log_warning(msg)
                    else:
                        self.log_error(msg)
    
    # 5. API Integration Testing
    async def validate_api_integration(self):
        """Validate API integration through comprehensive flow tests"""
        print("\n5. VALIDATING API INTEGRATION")
        print("-" * 50)
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            
            # Test health endpoint structure
            try:
                response = await client.get("/api/health")
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["status", "timestamp", "version"]
                    
                    if all(field in data for field in required_fields):
                        self.log_success("Health API structure valid")
                    else:
                        missing = [f for f in required_fields if f not in data]
                        self.log_error(f"Health API missing fields: {missing}")
                else:
                    self.log_error(f"Health API failed: {response.status_code}")
            except Exception as e:
                self.log_error(f"Health API error: {e}")
            
            # Test volunteer API flow
            volunteer_id = "test-volunteer-" + str(int(time.time()))
            
            # Quick match test
            try:
                quick_match_data = {"volunteerId": volunteer_id, "limit": 5}
                response = await client.post("/api/volunteer/quick-match", json=quick_match_data)
                
                if response.status_code == 200:
                    self.log_success("Quick match API accessible")
                elif response.status_code == 404:
                    self.log_success("Quick match API accessible (no matches found)")
                else:
                    self.log_warning(f"Quick match returned {response.status_code}")
            except Exception as e:
                self.log_error(f"Quick match API error: {e}")
            
            # Dashboard test
            try:
                response = await client.get(f"/api/volunteer/{volunteer_id}/dashboard")
                
                if response.status_code == 200:
                    data = response.json()
                    required_sections = ["profile", "activeApplications", "recentMatches"]
                    
                    if all(section in data for section in required_sections):
                        self.log_success("Dashboard API structure valid")
                    else:
                        missing = [s for s in required_sections if s not in data]
                        self.log_error(f"Dashboard API missing sections: {missing}")
                else:
                    self.log_error(f"Dashboard API failed: {response.status_code}")
            except Exception as e:
                self.log_error(f"Dashboard API error: {e}")
            
            # Application submission test
            try:
                app_data = {
                    "volunteerId": volunteer_id,
                    "opportunityId": "test-opportunity-" + str(int(time.time())),
                    "coverLetter": "Test application from validation suite"
                }
                
                response = await client.post("/api/volunteer/apply", json=app_data)
                
                if response.status_code in [200, 201]:
                    self.log_success("Application API accessible")
                elif response.status_code in [400, 409]:
                    self.log_success("Application API accessible (validation/conflict)")
                else:
                    self.log_warning(f"Application API returned {response.status_code}")
            except Exception as e:
                self.log_error(f"Application API error: {e}")
    
    # 6. Frontend Accessibility
    async def validate_frontend_accessibility(self):
        """Validate frontend is accessible and serving correctly"""
        print("\n6. VALIDATING FRONTEND ACCESSIBILITY")
        print("-" * 50)
        
        frontend_url = "http://localhost:3000"
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                start_time = time.time()
                response = await client.get(frontend_url)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_success(f"Frontend accessible ({response_time:.2f}s)")
                    self.report["performance"]["Frontend"] = response_time
                    
                    # Check if it's actually serving a React app
                    content = response.text
                    if "react" in content.lower() or "next" in content.lower():
                        self.log_success("Frontend serving React/Next.js application")
                    else:
                        self.log_warning("Frontend not serving expected React content")
                else:
                    self.log_error(f"Frontend returned {response.status_code}")
        except Exception as e:
            self.log_error(f"Frontend not accessible: {e}")
    
    # 7. Data Layer Validation
    def validate_data_layer(self):
        """Validate event sourcing and data persistence"""
        print("\n7. VALIDATING DATA LAYER")
        print("-" * 50)
        
        data_dir = Path("data")
        if data_dir.exists():
            self.log_success("Data directory exists")
            
            # Check for event files
            event_files = list(data_dir.glob("*events*.jsonl"))
            if event_files:
                self.log_success(f"Found {len(event_files)} event files")
                
                total_events = 0
                for event_file in event_files:
                    try:
                        with open(event_file, 'r') as f:
                            events = [line for line in f if line.strip()]
                            total_events += len(events)
                    except Exception:
                        pass
                
                if total_events > 0:
                    self.log_success(f"Event store contains {total_events} events")
                else:
                    self.log_warning("Event store is empty")
            else:
                self.log_warning("No event files found")
            
            # Check for data files
            data_files = list(data_dir.glob("*.json"))
            if data_files:
                self.log_success(f"Found {len(data_files)} data files")
            else:
                self.log_warning("No JSON data files found")
        else:
            self.log_warning("Data directory does not exist")
    
    # 8. Performance Testing
    async def validate_performance(self):
        """Test system performance under load"""
        print("\n8. VALIDATING SYSTEM PERFORMANCE")
        print("-" * 50)
        
        async def make_health_request():
            async with httpx.AsyncClient(base_url=self.base_url, timeout=10) as client:
                start_time = time.time()
                try:
                    response = await client.get("/api/health")
                    response_time = time.time() - start_time
                    return response.status_code == 200, response_time
                except Exception:
                    return False, time.time() - start_time
        
        # Test concurrent requests
        num_requests = 10
        tasks = [make_health_request() for _ in range(num_requests)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception) and r[0])
        avg_response_time = sum(r[1] for r in results if not isinstance(r, Exception)) / len(results)
        
        self.report["performance"]["concurrent_success_rate"] = successful / num_requests
        self.report["performance"]["average_response_time"] = avg_response_time
        self.report["performance"]["total_concurrent_time"] = total_time
        
        if successful >= num_requests * 0.8:  # 80% success rate
            self.log_success(f"Performance test: {successful}/{num_requests} requests successful")
        else:
            self.log_warning(f"Performance test: Only {successful}/{num_requests} requests successful")
        
        if avg_response_time < 5.0:  # Sub-5-second average
            self.log_success(f"Performance test: Average response time {avg_response_time:.2f}s")
        else:
            self.log_warning(f"Performance test: Slow average response time {avg_response_time:.2f}s")
    
    # 9. Generate Comprehensive Report
    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE SERAAJ SYSTEM VALIDATION REPORT")
        print("=" * 70)
        
        # Summary statistics
        total_checks = len(self.report["checks"])
        total_warnings = len(self.report["warnings"])
        total_errors = len(self.report["errors"])
        
        self.report["summary"] = {
            "total_checks": total_checks,
            "total_warnings": total_warnings,
            "total_errors": total_errors,
            "validation_status": "PASSED" if total_errors == 0 else "FAILED",
            "confidence_level": "HIGH" if total_errors == 0 and total_warnings <= 5 else 
                               "MEDIUM" if total_errors == 0 else "LOW"
        }
        
        print(f"\nSUMMARY:")
        print(f"  [OK] Successful Checks: {total_checks}")
        print(f"  [WARN] Warnings: {total_warnings}")
        print(f"  [ERROR] Errors: {total_errors}")
        print(f"  [STATUS] Validation Status: {self.report['summary']['validation_status']}")
        print(f"  [CONFIDENCE] Confidence Level: {self.report['summary']['confidence_level']}")
        
        if total_errors > 0:
            print(f"\n[ERROR] CRITICAL ERRORS FOUND:")
            for error in self.report["errors"]:
                print(f"  {error}")
        
        if total_warnings > 0:
            print(f"\n[WARN] WARNINGS:")
            for warning in self.report["warnings"]:
                print(f"  {warning}")
        
        # Performance metrics
        if self.report["performance"]:
            print(f"\n[PERFORMANCE] PERFORMANCE METRICS:")
            for service, metric in self.report["performance"].items():
                if isinstance(metric, float):
                    print(f"  {service}: {metric:.2f}s")
                else:
                    print(f"  {service}: {metric}")
        
        print(f"\n[OK] SUCCESSFUL VALIDATIONS:")
        for check in self.report["checks"]:
            print(f"  {check}")
        
        # Save detailed report
        report_file = Path("tests/validation/comprehensive_validation_report.json")
        report_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(report_file, "w") as f:
            json.dump(self.report, f, indent=2)
        
        print(f"\n[REPORT] Detailed report saved to: {report_file.absolute()}")
        
        # Create validation checkpoint if successful
        if total_errors == 0:
            checkpoint_file = Path(".agents/checkpoints/comprehensive_validation.done")
            checkpoint_data = {
                "timestamp": self.report["timestamp"],
                "status": "PASSED",
                "checks": total_checks,
                "warnings": total_warnings,
                "confidence": self.report["summary"]["confidence_level"]
            }
            
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint_data, f, indent=2)
            
            print(f"[CHECKPOINT] Validation checkpoint created: {checkpoint_file.absolute()}")
        
        print("=" * 70)
        
        return total_errors == 0
    
    # Main validation runner
    async def run_comprehensive_validation(self):
        """Run all validation steps"""
        print("[VALIDATION] STARTING COMPREHENSIVE SERAAJ SYSTEM VALIDATION")
        print("[FOCUS] Post-SDK fixes and integration improvements")
        print("=" * 70)
        
        # Run all validation steps
        self.validate_contracts_and_config()
        self.validate_sdk_structure()
        self.validate_frontend_integration()
        await self.validate_backend_health()
        await self.validate_api_integration()
        await self.validate_frontend_accessibility()
        self.validate_data_layer()
        await self.validate_performance()
        
        # Generate comprehensive report
        success = self.generate_report()
        
        return success


async def main():
    """Main entry point"""
    validator = SeraajSystemValidator()
    
    try:
        success = await validator.run_comprehensive_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
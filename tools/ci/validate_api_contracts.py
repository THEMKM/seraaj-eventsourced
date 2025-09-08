#!/usr/bin/env python3
"""
API Contract Validation Tool for CI/CD Pipeline

Validates that API responses conform to OpenAPI specifications.
This ensures services maintain contract compliance across deployments.
"""

import httpx
import json
import jsonschema
import yaml
from pathlib import Path
import sys
import os
import time
from typing import Dict, Any, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIContractValidator:
    """Validates API endpoints against OpenAPI contracts"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=30.0)
        
    def load_openapi_spec(self, spec_path: str) -> dict:
        """Load and parse OpenAPI specification"""
        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
                    return yaml.safe_load(f)
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load OpenAPI spec from {spec_path}: {e}")
            return {}
    
    def load_referenced_schemas(self, schemas_dir: Path) -> Dict[str, Any]:
        """Load all referenced schema files"""
        referenced_schemas = {}
        
        if not schemas_dir.exists():
            logger.warning(f"Schemas directory not found: {schemas_dir}")
            return referenced_schemas
            
        for schema_file in schemas_dir.glob("*.yaml"):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_content = yaml.safe_load(f)
                    ref_path = f"./schemas/{schema_file.name}"
                    referenced_schemas[ref_path] = schema_content
                    logger.debug(f"Loaded schema: {ref_path}")
            except Exception as e:
                logger.warning(f"Failed to load schema {schema_file}: {e}")
                
        return referenced_schemas
    
    def resolve_schema_ref(self, schema_ref: str, openapi_spec: dict, referenced_schemas: dict) -> Dict[str, Any]:
        """Resolve a schema reference to actual schema definition"""
        if schema_ref.startswith('./schemas/'):
            return referenced_schemas.get(schema_ref, {})
        elif schema_ref.startswith('#/components/schemas/'):
            component_name = schema_ref.split('/')[-1]
            return openapi_spec.get('components', {}).get('schemas', {}).get(component_name, {})
        return {}
    
    def validate_endpoint_response(self, method: str, path: str, 
                                 expected_status: int, expected_schema: dict,
                                 test_data: dict = None) -> bool:
        """Validate a single endpoint response against schema"""
        try:
            url = f"{self.base_url}{path}"
            logger.info(f"Testing {method.upper()} {url}")
            
            # Make the request
            if method.upper() == 'GET':
                response = self.client.get(url)
            elif method.upper() == 'POST':
                response = self.client.post(url, json=test_data or {})
            elif method.upper() == 'PUT':
                response = self.client.put(url, json=test_data or {})
            elif method.upper() == 'DELETE':
                response = self.client.delete(url)
            else:
                logger.warning(f"Method {method} not supported, skipping")
                return True
                
            # Check status code
            if response.status_code != expected_status:
                logger.error(f"❌ {method} {path}: Expected {expected_status}, got {response.status_code}")
                logger.debug(f"Response: {response.text[:500]}")
                return False
                
            # Skip schema validation if no content expected
            if expected_status == 204 or not expected_schema:
                logger.info(f"✅ {method} {path}: Status check passed (no content validation)")
                return True
                
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"❌ {method} {path}: Invalid JSON response: {e}")
                return False
            
            # Validate against schema
            jsonschema.validate(response_data, expected_schema)
            logger.info(f"✅ {method} {path}: Contract validation passed")
            return True
            
        except jsonschema.ValidationError as e:
            logger.error(f"❌ {method} {path}: Schema validation failed")
            logger.error(f"   Error: {e.message}")
            logger.error(f"   Path: {e.json_path}")
            logger.debug(f"   Response sample: {str(response_data)[:300] if 'response_data' in locals() else 'N/A'}")
            return False
        except httpx.RequestError as e:
            logger.error(f"❌ {method} {path}: Request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ {method} {path}: Unexpected error: {e}")
            return False

def wait_for_service(url: str, timeout: int = 60) -> bool:
    """Wait for a service to become available"""
    logger.info(f"Waiting for service at {url}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                logger.info(f"✅ Service ready at {url}")
                return True
        except Exception as e:
            logger.debug(f"Service not ready: {e}")
            time.sleep(2)
    
    logger.error(f"❌ Service at {url} not ready after {timeout}s")
    return False

def main():
    """Main contract validation function"""
    base_url = os.getenv('BFF_BASE_URL', 'http://127.0.0.1:8000')
    logger.info(f"Starting API contract validation against {base_url}")
    
    # Wait for BFF service to be ready
    if not wait_for_service(f"{base_url}/api/health"):
        sys.exit(1)
    
    # Initialize validator
    validator = APIContractValidator(base_url)
    
    # Load OpenAPI specifications
    contracts_dir = Path(__file__).parent.parent.parent / "contracts" / "v1.1.0" / "api"
    bff_spec_path = contracts_dir / "bff.openapi.yaml"
    schemas_dir = contracts_dir / "schemas"
    
    if not bff_spec_path.exists():
        logger.error(f"BFF OpenAPI spec not found: {bff_spec_path}")
        sys.exit(1)
    
    # Load specifications
    bff_spec = validator.load_openapi_spec(str(bff_spec_path))
    referenced_schemas = validator.load_referenced_schemas(schemas_dir)
    
    if not bff_spec:
        logger.error("Failed to load BFF OpenAPI specification")
        sys.exit(1)
    
    logger.info(f"Loaded BFF spec with {len(bff_spec.get('paths', {}))} endpoints")
    logger.info(f"Loaded {len(referenced_schemas)} referenced schemas")
    
    # Define test cases based on available endpoints
    test_cases = [
        {
            'method': 'GET',
            'path': '/api/health',
            'expected_status': 200,
            'schema_path': ['paths', '/health', 'get', 'responses', '200', 'content', 'application/json', 'schema']
        },
        {
            'method': 'GET', 
            'path': '/api/health/services',
            'expected_status': 200,
            'schema_path': ['paths', '/health/services', 'get', 'responses', '200', 'content', 'application/json', 'schema']
        }
    ]
    
    # Add additional test cases if endpoints exist in spec
    paths = bff_spec.get('paths', {})
    if '/volunteer/quick-match' in paths:
        test_cases.append({
            'method': 'POST',
            'path': '/api/volunteer/quick-match',
            'expected_status': 200,
            'schema_path': ['paths', '/volunteer/quick-match', 'post', 'responses', '200', 'content', 'application/json', 'schema'],
            'test_data': {
                'volunteerId': 'test-volunteer-001',
                'limit': 5
            }
        })
    
    logger.info(f"Running {len(test_cases)} contract validation tests...")
    
    # Run validation tests
    all_passed = True
    passed_count = 0
    
    for i, test in enumerate(test_cases):
        logger.info(f"Test {i+1}/{len(test_cases)}: {test['method']} {test['path']}")
        
        # Extract schema from spec
        schema = bff_spec
        try:
            for path_part in test['schema_path']:
                schema = schema[path_part]
        except KeyError as e:
            logger.warning(f"Schema path not found: {test['schema_path']} (missing: {e})")
            continue
        
        # Resolve schema references
        if isinstance(schema, dict) and '$ref' in schema:
            resolved_schema = validator.resolve_schema_ref(schema['$ref'], bff_spec, referenced_schemas)
            if resolved_schema:
                schema = resolved_schema
                
        # Run the test
        passed = validator.validate_endpoint_response(
            test['method'],
            test['path'],
            test['expected_status'],
            schema,
            test.get('test_data')
        )
        
        if passed:
            passed_count += 1
        else:
            all_passed = False
    
    # Print summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Contract Validation Summary")
    logger.info(f"{'='*50}")
    logger.info(f"Total tests: {len(test_cases)}")
    logger.info(f"Passed: {passed_count}")
    logger.info(f"Failed: {len(test_cases) - passed_count}")
    
    if all_passed:
        logger.info("✅ All API contract validations passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some API contract validations failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
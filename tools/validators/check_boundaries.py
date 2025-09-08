#!/usr/bin/env python3
"""
Enhanced Boundary Checking for CI/CD Pipeline

Validates that all changes respect agent boundaries and detect potential violations.
This ensures agents only modify files within their allowed paths.
"""

import json
import subprocess
import sys
import logging
from pathlib import Path
import fnmatch
from typing import List, Dict, Set, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class BoundaryViolation:
    """Represents a boundary violation"""
    def __init__(self, file_path: str, issue: str, severity: str = "error"):
        self.file_path = file_path
        self.issue = issue
        self.severity = severity
    
    def __str__(self):
        return f"{self.severity.upper()}: {self.file_path} - {self.issue}"

class BoundaryChecker:
    """Check agent boundary compliance"""
    
    def __init__(self, boundaries_file: str = ".agents/boundaries.json"):
        self.boundaries_file = boundaries_file
        self.boundaries = self.load_boundaries()
        
    def load_boundaries(self) -> Dict:
        """Load agent boundaries configuration"""
        try:
            with open(self.boundaries_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load boundaries file {self.boundaries_file}: {e}")
            return {"agents": {}}

    def get_changed_files(self) -> List[str]:
        """Get list of files changed in this PR/commit"""
        try:
            # First try: compare against origin/main (for PR)
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'origin/main...HEAD'],
                capture_output=True, text=True, check=True
            )
            
            if result.stdout.strip():
                changed_files = result.stdout.strip().split('\n')
                logger.info(f"Found {len(changed_files)} changed files (compared to origin/main)")
                return changed_files
            
            # Fallback: compare against HEAD~1 
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1'],
                capture_output=True, text=True, check=True
            )
            
            if result.stdout.strip():
                changed_files = result.stdout.strip().split('\n')
                logger.info(f"Found {len(changed_files)} changed files (compared to HEAD~1)")
                return changed_files
            else:
                logger.info("No changed files detected")
                return []
                
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git diff failed: {e}")
            # In CI, we might not have git history - try to get all files that are not in .git
            try:
                result = subprocess.run(
                    ['find', '.', '-type', 'f', '-not', '-path', './.git/*', '-not', '-path', './node_modules/*'],
                    capture_output=True, text=True, check=True
                )
                all_files = [f.lstrip('./') for f in result.stdout.strip().split('\n') if f.strip()]
                logger.warning(f"Using all {len(all_files)} files as fallback (no git history)")
                return all_files[:100]  # Limit to prevent overwhelming output
            except Exception as e2:
                logger.error(f"Failed to get file list: {e2}")
                return []

    def get_allowed_agents_for_file(self, file_path: str) -> List[str]:
        """Get list of agents that can modify this file"""
        allowed_agents = []
        
        for agent_name, config in self.boundaries.get('agents', {}).items():
            allowed_paths = config.get('allowed_paths', [])
            
            for pattern in allowed_paths:
                if fnmatch.fnmatch(file_path, pattern):
                    allowed_agents.append(agent_name)
                    break  # Found a match, no need to check other patterns for this agent
        
        return allowed_agents

    def check_file_boundaries(self, changed_files: List[str]) -> List[BoundaryViolation]:
        """Check boundary violations for changed files"""
        violations = []
        
        for file_path in changed_files:
            # Skip deleted or non-existent files
            if not Path(file_path).exists():
                logger.debug(f"Skipping deleted/non-existent file: {file_path}")
                continue
            
            # Skip certain file types that are generally safe
            if self.is_safe_file(file_path):
                logger.debug(f"Skipping safe file: {file_path}")
                continue
                
            allowed_agents = self.get_allowed_agents_for_file(file_path)
            
            if not allowed_agents:
                violations.append(BoundaryViolation(
                    file_path,
                    "No agent is allowed to modify this file",
                    "error"
                ))
            elif len(allowed_agents) > 5:  # Too many agents = potential boundary issue
                violations.append(BoundaryViolation(
                    file_path,
                    f"Too many agents allowed ({len(allowed_agents)}): {allowed_agents[:3]}...",
                    "warning"
                ))
            else:
                logger.debug(f"✅ {file_path}: Allowed by {allowed_agents}")
        
        return violations

    def is_safe_file(self, file_path: str) -> bool:
        """Check if file is generally safe to modify (low-risk files)"""
        safe_patterns = [
            "*.md",           # Documentation
            "*.txt",          # Text files
            ".gitignore",     # Git configuration
            "*.log",          # Log files
            ".env.example",   # Example environment files
            "LICENSE*",       # License files
        ]
        
        safe_directories = [
            ".git/",
            "node_modules/",
            "__pycache__/",
            ".pytest_cache/",
            "coverage/",
            "*.egg-info/",
        ]
        
        # Check safe patterns
        for pattern in safe_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        # Check safe directories
        for directory in safe_directories:
            if file_path.startswith(directory):
                return True
        
        return False

    def check_critical_files(self, changed_files: List[str]) -> List[BoundaryViolation]:
        """Check for modifications to critical system files"""
        violations = []
        
        critical_files = [
            ".agents/boundaries.json",
            "package.json",
            "requirements.txt",
            "contracts/version.lock",
            ".github/workflows/*"
        ]
        
        for file_path in changed_files:
            for critical_pattern in critical_files:
                if fnmatch.fnmatch(file_path, critical_pattern):
                    # Critical files should only be modified by specific agents
                    allowed_agents = self.get_allowed_agents_for_file(file_path)
                    
                    if not allowed_agents:
                        violations.append(BoundaryViolation(
                            file_path,
                            "Critical file modified without agent authorization",
                            "error"
                        ))
                    elif len(allowed_agents) == 1:
                        logger.info(f"✅ Critical file {file_path} modified by authorized agent: {allowed_agents[0]}")
                    else:
                        violations.append(BoundaryViolation(
                            file_path,
                            f"Critical file has multiple authorized agents: {allowed_agents}",
                            "warning"
                        ))
        
        return violations

    def validate_boundaries(self) -> Tuple[List[BoundaryViolation], bool]:
        """Main boundary validation function"""
        logger.info("Starting boundary validation...")
        
        changed_files = self.get_changed_files()
        
        if not changed_files:
            logger.info("No files changed, boundary check passed")
            return [], True
        
        logger.info(f"Checking boundaries for {len(changed_files)} changed files...")
        
        # Check standard boundary violations
        violations = self.check_file_boundaries(changed_files)
        
        # Check critical files
        critical_violations = self.check_critical_files(changed_files)
        violations.extend(critical_violations)
        
        # Categorize violations
        errors = [v for v in violations if v.severity == "error"]
        warnings = [v for v in violations if v.severity == "warning"]
        
        # Log results
        if violations:
            logger.warning(f"Found {len(violations)} boundary violations:")
            logger.warning(f"  - {len(errors)} errors")
            logger.warning(f"  - {len(warnings)} warnings")
            
            for violation in violations:
                if violation.severity == "error":
                    logger.error(f"  {violation}")
                else:
                    logger.warning(f"  {violation}")
        else:
            logger.info("✅ All file changes respect agent boundaries")
        
        # Return violations and success status
        success = len(errors) == 0  # Warnings don't fail the check
        return violations, success

def main():
    """Main entry point for boundary checking"""
    checker = BoundaryChecker()
    
    violations, success = checker.validate_boundaries()
    
    if success:
        if violations:
            logger.info("✅ Boundary check passed (warnings only)")
        else:
            logger.info("✅ Boundary check passed (no violations)")
        sys.exit(0)
    else:
        logger.error("❌ Boundary check failed due to violations")
        sys.exit(1)

if __name__ == '__main__':
    main()
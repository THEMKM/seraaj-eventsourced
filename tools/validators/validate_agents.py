#!/usr/bin/env python3
"""
Validate Claude Code sub-agent definitions
"""
import re
from pathlib import Path

def validate_agent_format(agent_file: Path) -> bool:
    """Validate a single agent file format"""
    try:
        content = agent_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            content = agent_file.read_text(encoding='utf-8', errors='replace')
        except Exception:
            print(f"ERROR {agent_file.name}: Cannot read file")
            return False
    
    # Check for required YAML front matter
    yaml_pattern = r'^---\n.*?^---\n'
    yaml_match = re.match(yaml_pattern, content, re.MULTILINE | re.DOTALL)
    
    if not yaml_match:
        print(f"ERROR {agent_file.name}: Missing YAML front matter")
        return False
    
    yaml_content = yaml_match.group(0)
    
    # Check required fields
    required_fields = ['name:', 'description:', 'tools:']
    for field in required_fields:
        if field not in yaml_content:
            print(f"ERROR {agent_file.name}: Missing required field '{field}'")
            return False
    
    # Check name format (lowercase with hyphens)
    name_match = re.search(r'name:\s*([^\n]+)', yaml_content)
    if name_match:
        name = name_match.group(1).strip()
        if not re.match(r'^[a-z-]+$', name):
            print(f"ERROR {agent_file.name}: Name should be lowercase with hyphens: '{name}'")
            return False
    
    # Check description is present and meaningful
    desc_match = re.search(r'description:\s*([^\n]+(?:\n\s+[^\n]+)*)', yaml_content)
    if desc_match:
        description = desc_match.group(1).strip()
        if len(description) < 20:
            print(f"ERROR {agent_file.name}: Description too short: '{description}'")
            return False
    
    # Check tools are specified
    tools_match = re.search(r'tools:\s*([^\n]+)', yaml_content)
    if tools_match:
        tools = tools_match.group(1).strip()
        if not tools or tools == '':
            print(f"ERROR {agent_file.name}: No tools specified")
            return False
    
    # Check system prompt exists after YAML
    system_prompt = content[yaml_match.end():].strip()
    if len(system_prompt) < 100:
        print(f"ERROR {agent_file.name}: System prompt too short")
        return False
    
    # Check for boundary definitions
    if "Strict Boundaries" not in system_prompt and "Boundaries" not in system_prompt:
        print(f"WARNING {agent_file.name}: No boundary definitions found")
    
    # Check for prerequisites
    if "Prerequisites" not in system_prompt:
        print(f"WARNING {agent_file.name}: No prerequisites section found")
    
    print(f"VALID {agent_file.name}: Valid format")
    return True

def main():
    """Validate all agent definitions"""
    agents_dir = Path(".claude/agents")
    
    if not agents_dir.exists():
        print("ERROR: No .claude/agents directory found")
        return False
    
    agent_files = list(agents_dir.glob("*.md"))
    if "README.md" in [f.name for f in agent_files]:
        agent_files = [f for f in agent_files if f.name != "README.md"]
    
    if not agent_files:
        print("ERROR: No agent definition files found")
        return False
    
    print(f"Validating {len(agent_files)} agent definitions...")
    print("=" * 50)
    
    all_valid = True
    for agent_file in sorted(agent_files):
        if not validate_agent_format(agent_file):
            all_valid = False
    
    print("=" * 50)
    
    if all_valid:
        print(f"SUCCESS: All {len(agent_files)} agent definitions are valid!")
        
        # List agents in execution order
        expected_agents = [
            "contract-architect.md",
            "generator.md", 
            "service-builder-applications.md",
            "service-builder-matching.md",
            "orchestrator.md",
            "validator.md"
        ]
        
        found_agents = [f.name for f in agent_files]
        missing = [a for a in expected_agents if a not in found_agents]
        extra = [a for a in found_agents if a not in expected_agents]
        
        if missing:
            print(f"WARNING: Missing expected agents: {missing}")
        if extra:
            print(f"INFO: Additional agents found: {extra}")
        
        print("\nExecution Sequence:")
        for i, agent in enumerate(expected_agents, 1):
            if agent in found_agents:
                print(f"  {i}. {agent.replace('.md', '').replace('-', ' ').title()}")
            else:
                print(f"  {i}. {agent} (MISSING)")
        
        return True
    else:
        print("ERROR: Some agent definitions have issues")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
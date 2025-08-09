#!/bin/bash

# Seraaj Development Watcher
# Non-blocking warnings for boundary violations, SDK changes, and forbidden HTTP usage

set -e

# Colors for output  
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}[SERAAJ-WATCH] 👁️  Starting development watcher...${NC}"
echo -e "${BLUE}[SERAAJ-WATCH] Project root: $PROJECT_ROOT${NC}"

# Get current agent from environment
CURRENT_AGENT=${SERAJ_AGENT:-"FRONTEND_COMPOSER"}
echo -e "${BLUE}[SERAAJ-WATCH] Current agent: $CURRENT_AGENT${NC}"

# Read boundaries
BOUNDARIES_FILE="$PROJECT_ROOT/.agents/boundaries.json"
if [[ ! -f "$BOUNDARIES_FILE" ]]; then
    echo -e "${RED}[SERAAJ-WATCH] ⚠️  Missing boundaries file${NC}"
    exit 1
fi

# Get allowed paths for current agent
ALLOWED_PATHS=$(python3 -c "
import json
import sys
try:
    with open('$BOUNDARIES_FILE') as f:
        boundaries = json.load(f)
    agent_config = boundaries.get('agents', {}).get('$CURRENT_AGENT', {})
    allowed_paths = agent_config.get('allowed_paths', [])
    for path in allowed_paths:
        print(path)
except Exception as e:
    print('Error reading boundaries:', str(e), file=sys.stderr)
    sys.exit(1)
")

if [[ -z "$ALLOWED_PATHS" ]]; then
    echo -e "${RED}[SERAAJ-WATCH] ⚠️  No allowed paths found for agent: $CURRENT_AGENT${NC}"
    exit 1
fi

echo -e "${BLUE}[SERAAJ-WATCH] Allowed paths:${NC}"
while IFS= read -r path; do
    echo -e "${BLUE}  - $path${NC}"
done <<< "$ALLOWED_PATHS"

# Function to check if a path matches allowed patterns
path_allowed() {
    local file_path="$1"
    while IFS= read -r allowed_pattern; do
        if [[ "$file_path" == $allowed_pattern ]]; then
            return 0
        fi
    done <<< "$ALLOWED_PATHS"
    return 1
}

# Function to check for forbidden HTTP usage
check_forbidden_http() {
    local file_path="$1"
    if [[ "$file_path" == *.ts || "$file_path" == *.tsx ]]; then
        if [[ -f "$PROJECT_ROOT/$file_path" ]]; then
            # Check for forbidden patterns
            local forbidden_count=0
            forbidden_count=$(grep -n -E "(\\bfetch\\s*\\(|\\baxios\\.|\\bky\\.|\\bsuperagent\\.|from [\"']axios[\"']|from [\"']ky[\"']|import.*axios|import.*ky)" "$PROJECT_ROOT/$file_path" 2>/dev/null | wc -l || echo "0")
            
            if [[ $forbidden_count -gt 0 ]]; then
                echo -e "${YELLOW}[SERAAJ-WATCH] ⚠️  Forbidden HTTP usage detected in: $file_path${NC}"
                grep -n -E "(\\bfetch\\s*\\(|\\baxios\\.|\\bky\\.|\\bsuperagent\\.|from [\"']axios[\"']|from [\"']ky[\"']|import.*axios|import.*ky)" "$PROJECT_ROOT/$file_path" 2>/dev/null | head -3 | while IFS= read -r line; do
                    echo -e "${YELLOW}    $line${NC}"
                done
            fi
        fi
    fi
}

# Function to check for forbidden deep SDK imports
check_forbidden_sdk_imports() {
    local file_path="$1"
    if [[ "$file_path" == *.ts || "$file_path" == *.tsx ]]; then
        if [[ -f "$PROJECT_ROOT/$file_path" ]]; then
            local deep_imports=0
            deep_imports=$(grep -n -E "(from [\"']@seraaj/sdk-bff/src/|import.*@seraaj/sdk-bff/src/)" "$PROJECT_ROOT/$file_path" 2>/dev/null | wc -l || echo "0")
            
            if [[ $deep_imports -gt 0 ]]; then
                echo -e "${YELLOW}[SERAAJ-WATCH] ⚠️  Forbidden deep SDK import in: $file_path${NC}"
                grep -n -E "(from [\"']@seraaj/sdk-bff/src/|import.*@seraaj/sdk-bff/src/)" "$PROJECT_ROOT/$file_path" 2>/dev/null | while IFS= read -r line; do
                    echo -e "${YELLOW}    $line${NC}"
                done
            fi
        fi
    fi
}

# Function to watch for file changes
watch_files() {
    echo -e "${BLUE}[SERAAJ-WATCH] 👀 Watching for file changes... (Ctrl+C to stop)${NC}"
    
    # Use inotifywait if available, otherwise fall back to polling
    if command -v inotifywait >/dev/null 2>&1; then
        # Use inotifywait for real-time monitoring
        inotifywait -m -r "$PROJECT_ROOT" \
            --exclude '(\.git|node_modules|\.next|dist|build|\.tmp)' \
            -e modify,create,move \
            --format '%w%f' 2>/dev/null | while read -r changed_file; do
            
            # Make path relative to project root
            rel_path="${changed_file#$PROJECT_ROOT/}"
            
            # Skip if file doesn't exist (might be temporary)
            if [[ ! -f "$changed_file" ]]; then
                continue
            fi
            
            # Check boundary violations
            if ! path_allowed "$rel_path"; then
                echo -e "${YELLOW}[SERAAJ-WATCH] ⚠️  Boundary violation: $rel_path (not allowed for $CURRENT_AGENT)${NC}"
            fi
            
            # Check for forbidden HTTP patterns
            if [[ "$rel_path" == apps/web/* ]]; then
                check_forbidden_http "$rel_path"
                check_forbidden_sdk_imports "$rel_path"
            fi
            
            # SDK change warnings
            if [[ "$rel_path" == packages/sdk-bff/* ]]; then
                echo -e "${YELLOW}[SERAAJ-WATCH] ⚠️  SDK file changed: $rel_path${NC}"
                if [[ "$CURRENT_AGENT" == "FRONTEND_COMPOSER" ]]; then
                    echo -e "${YELLOW}    Note: FRONTEND_COMPOSER should not modify SDK files${NC}"
                fi
            fi
            
            # Contract changes
            if [[ "$rel_path" == contracts/* ]]; then
                echo -e "${YELLOW}[SERAAJ-WATCH] ⚠️  Contract file changed: $rel_path${NC}"
                echo -e "${YELLOW}    Note: SDK may need regeneration${NC}"
            fi
        done
    else
        echo -e "${YELLOW}[SERAAJ-WATCH] inotifywait not available, using polling mode${NC}"
        
        # Polling fallback
        while true; do
            sleep 2
            
            # Simple check for recent modifications in watched directories
            find "$PROJECT_ROOT" -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" 2>/dev/null | \
            grep -v -E "(node_modules|\.git|\.next|dist|build)" | \
            while IFS= read -r file; do
                rel_path="${file#$PROJECT_ROOT/}"
                
                # Check if file was modified in last 3 seconds
                if [[ $(find "$file" -mtime -3s 2>/dev/null) ]]; then
                    if [[ "$rel_path" == apps/web/* ]]; then
                        check_forbidden_http "$rel_path"
                        check_forbidden_sdk_imports "$rel_path" 
                    fi
                fi
            done
        done
    fi
}

# Start watching
cd "$PROJECT_ROOT"
trap 'echo -e "${BLUE}[SERAAJ-WATCH] 👋 Stopping watcher...${NC}"; exit 0' INT
watch_files
#!/bin/bash
# Script to migrate from projects.yaml to sessions/*.yaml structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Migrating projects.yaml to sessions/*.yaml structure${NC}"

# Check if projects.yaml exists
if [ ! -f "projects.yaml" ]; then
    echo -e "${RED}Error: projects.yaml not found${NC}"
    exit 1
fi

# Create sessions directory if it doesn't exist
mkdir -p sessions

# Check if yq is installed
if ! command -v yq &> /dev/null; then
    echo -e "${YELLOW}Installing yq for YAML processing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install yq
    else
        sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
        sudo chmod +x /usr/local/bin/yq
    fi
fi

# Extract sessions from projects.yaml
echo -e "${YELLOW}Extracting sessions from projects.yaml...${NC}"

# Get all session names
session_names=$(yq eval '.sessions | keys | .[]' projects.yaml)

# Counter for migrated sessions
count=0

# Process each session
while IFS= read -r session_name; do
    if [ -z "$session_name" ]; then
        continue
    fi
    
    echo -e "Processing session: ${GREEN}$session_name${NC}"
    
    # Extract session configuration
    session_config=$(yq eval ".sessions.\"$session_name\"" projects.yaml)
    
    # Determine output directory based on session name
    if [[ "$session_name" == *"prod"* ]] || [[ "$session_name" == *"production"* ]]; then
        output_dir="sessions/production"
    elif [[ "$session_name" == *"test"* ]] || [[ "$session_name" == *"staging"* ]]; then
        output_dir="sessions/testing"
    elif [[ "$session_name" == *"data"* ]] || [[ "$session_name" == *"jupyter"* ]]; then
        output_dir="sessions/data"
    else
        output_dir="sessions/development"
    fi
    
    # Create directory if needed
    mkdir -p "$output_dir"
    
    # Write session configuration to file
    output_file="$output_dir/${session_name}.yaml"
    
    # Add session_name if not present in override
    if ! echo "$session_config" | grep -q "session_name:"; then
        echo "# Auto-migrated from projects.yaml" > "$output_file"
        echo "session_name: \"$session_name\"" >> "$output_file"
        echo "$session_config" >> "$output_file"
    else
        echo "# Auto-migrated from projects.yaml" > "$output_file"
        echo "$session_config" >> "$output_file"
    fi
    
    echo -e "  Created: ${GREEN}$output_file${NC}"
    ((count++))
done <<< "$session_names"

# Create a backup of projects.yaml
backup_file="projects.yaml.backup.$(date +%Y%m%d_%H%M%S)"
cp projects.yaml "$backup_file"
echo -e "${YELLOW}Backup created: $backup_file${NC}"

# Summary
echo -e "\n${GREEN}Migration completed!${NC}"
echo -e "  - Migrated ${GREEN}$count${NC} sessions"
echo -e "  - Original file backed up to: ${YELLOW}$backup_file${NC}"
echo -e "\nNext steps:"
echo -e "  1. Review the migrated files in ${GREEN}sessions/${NC}"
echo -e "  2. Test with: ${YELLOW}yesman ls${NC}"
echo -e "  3. If everything works, you can remove projects.yaml"
echo -e "\n${YELLOW}Note:${NC} You may need to adjust template references and paths"
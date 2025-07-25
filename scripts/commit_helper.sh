#!/bin/bash

# Commit Helper Script for Meaning-Based Organization
# This script helps organize changes according to commit prompt guidelines

set -e

echo "=== Commit Helper: Meaning-Based Organization ==="
echo

# Function to check if file should be excluded
should_exclude_file() {
    local file="$1"
    
    # Check common exclude patterns
    if [[ "$file" == *.DS_Store ]] || \
       [[ "$file" == .idea/* ]] || \
       [[ "$file" == .vscode/* ]] || \
       [[ "$file" == node_modules/* ]] || \
       [[ "$file" == __pycache__/* ]] || \
       [[ "$file" == *.log ]] || \
       [[ "$file" == *.tmp ]] || \
       [[ "$file" == .claude/* ]] || \
       [[ "$file" == .roocode/* ]] || \
       [[ "$file" == *.cache ]] || \
       [[ "$file" == .backups/* ]]; then
        return 0  # Should exclude
    fi
    
    return 1  # Should include
}

# Function to get commit type based on file content/pattern
get_commit_type() {
    local file="$1"
    
    # Test files
    if [[ "$file" == tests/* ]] || [[ "$file" == *test* ]]; then
        echo "test"
        return
    fi
    
    # Documentation files
    if [[ "$file" == docs/* ]] || [[ "$file" == *.md ]]; then
        echo "chore"
        return
    fi
    
    # Configuration files
    if [[ "$file" == config/* ]] || [[ "$file" == *.yaml ]] || [[ "$file" == *.toml ]] || [[ "$file" == Makefile* ]]; then
        echo "chore"
        return
    fi
    
    # API files
    if [[ "$file" == api/* ]]; then
        echo "feat"
        return
    fi
    
    # Core library files
    if [[ "$file" == libs/* ]]; then
        echo "refactor"
        return
    fi
    
    # Command files
    if [[ "$file" == commands/* ]]; then
        echo "feat"
        return
    fi
    
    # Default to refactor for other code changes
    echo "refactor"
}

# Function to generate commit message
generate_commit_message() {
    local commit_type="$1"
    local file="$2"
    
    # Extract meaningful description from file path
    local basename=$(basename "$file")
    local description=""
    
    # Remove extension and common prefixes
    description=$(echo "$basename" | sed 's/\.[^.]*$//' | sed 's/^test_//' | sed 's/^test-//' | sed 's/_/ /g' | sed 's/-/ /g')
    
    # Capitalize first letter
    description=$(echo "$description" | sed 's/^\(.\)/\U\1/')
    
    # Add context based on directory
    if [[ "$file" == api/routers/* ]]; then
        description="API router: $description"
    elif [[ "$file" == api/utils/* ]]; then
        description="API utility: $description"
    elif [[ "$file" == libs/dashboard/* ]]; then
        description="Dashboard: $description"
    elif [[ "$file" == libs/multi_agent/* ]]; then
        description="Multi-agent: $description"
    elif [[ "$file" == commands/* ]]; then
        description="Command: $description"
    fi
    
    echo "${commit_type}(claude): ${description}"
}

# Show current git status
echo "Current changes:"
git status --porcelain | head -20
if [ $(git status --porcelain | wc -l) -gt 20 ]; then
    echo "... and $(( $(git status --porcelain | wc -l) - 20 )) more files"
fi
echo

# Show total number of changes
total_changes=$(git status --porcelain | wc -l)
echo "Total files changed: $total_changes"
echo

# Interactive staging process
echo "=== Staging Process ==="
echo "1. Stage all non-excluded files"
echo "2. Review and selectively stage"
echo "3. Skip staging (use current staged files)"
echo

read -p "Choose staging option [1-3] (default: 1): " staging_option
staging_option=${staging_option:-1}

case $staging_option in
    1)
        echo "Staging all non-excluded files..."
        # Add all files first
        git add .
        
        # Remove excluded files
        git status --porcelain | while read line; do
            status=$(echo "$line" | cut -c1-2)
            file=$(echo "$line" | cut -c4-)
            
            if should_exclude_file "$file"; then
                echo "Excluding: $file"
                git reset "$file" >/dev/null 2>&1 || true
            fi
        done
        ;;
    2)
        echo "Reviewing files for staging..."
        git status --porcelain | while read line; do
            status=$(echo "$line" | cut -c1-2)
            file=$(echo "$line" | cut -c4-)
            
            if should_exclude_file "$file"; then
                echo "Skipping (excluded): $file"
                continue
            fi
            
            read -p "Stage $file? [Y/n/q] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Qq]$ ]]; then
                break
            elif [[ $REPLY =~ ^[Nn]$ ]]; then
                echo "Skipping: $file"
            else
                git add "$file"
                echo "Staged: $file"
            fi
        done
        ;;
    3)
        echo "Using currently staged files..."
        ;;
    *)
        echo "Invalid option, staging all non-excluded files..."
        git add .
        git status --porcelain | while read line; do
            status=$(echo "$line" | cut -c1-2)
            file=$(echo "$line" | cut -c4-)
            
            if should_exclude_file "$file"; then
                echo "Excluding: $file"
                git reset "$file" >/dev/null 2>&1 || true
            fi
        done
        ;;
esac

echo
echo "=== Staged Files ==="
staged_files=$(git diff --cached --name-only)
if [ -z "$staged_files" ]; then
    echo "No files staged for commit."
    exit 0
fi

echo "$staged_files" | head -10
if [ $(echo "$staged_files" | wc -l) -gt 10 ]; then
    echo "... and $(( $(echo "$staged_files" | wc -l) - 10 )) more files"
fi
echo

# Check if we want to make a single commit or split into multiple
read -p "Make single commit or split into multiple? [single/multiple] (default: single): " commit_type
commit_type=${commit_type:-single}

if [[ "$commit_type" == "multiple" ]]; then
    echo "=== Multiple Commit Mode ==="
    echo "Grouping files by commit type..."
    
    # Group files by type
    declare -A file_groups
    while IFS= read -r file; do
        commit_type=$(get_commit_type "$file")
        if [[ -z "${file_groups[$commit_type]}" ]]; then
            file_groups[$commit_type]="$file"
        else
            file_groups[$commit_type]="${file_groups[$commit_type]}|$file"
        fi
    done <<< "$staged_files"
    
    # Show groups
    echo "File groups:"
    for group in "${!file_groups[@]}"; do
        echo "  $group: $(echo "${file_groups[$group]}" | tr '|' '\n' | wc -l) files"
    done
    echo
    
    # Commit each group
    for group in "${!file_groups[@]}"; do
        echo "=== Committing $group changes ==="
        files=$(echo "${file_groups[$group]}" | tr '|' '\n')
        
        # Reset all staged files
        git reset >/dev/null 2>&1
        
        # Stage only this group
        echo "$files" | while read file; do
            if [ -n "$file" ]; then
                git add "$file"
            fi
        done
        
        # Generate commit message from first file
        first_file=$(echo "$files" | head -1)
        if [ -n "$first_file" ]; then
            commit_msg=$(generate_commit_message "$group" "$first_file")
            echo "Commit message: $commit_msg"
            
            read -p "Commit with this message? [Y/n/e] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Ee]$ ]]; then
                read -p "Enter custom message: " custom_msg
                commit_msg="$group(claude): $custom_msg"
            elif [[ ! $REPLY =~ ^[Nn]$ ]]; then
                git commit -m "$commit_msg"
                echo "Committed: $commit_msg"
            fi
        fi
    done
    
else
    echo "=== Single Commit Mode ==="
    # Generate commit message based on most common file type
    declare -A type_count
    while IFS= read -r file; do
        commit_type=$(get_commit_type "$file")
        ((type_count[$commit_type]++))
    done <<< "$staged_files"
    
    # Find most common type
    max_count=0
    main_type="refactor"
    for type in "${!type_count[@]}"; do
        if [ ${type_count[$type]} -gt $max_count ]; then
            max_count=${type_count[$type]}
            main_type=$type
        fi
    done
    
    echo "Main change type: $main_type ($(echo "$staged_files" | wc -l) files)"
    commit_msg=$(generate_commit_message "$main_type" "multiple files")
    
    # Truncate if too long
    if [ ${#commit_msg} -gt 50 ]; then
        commit_msg="${commit_msg:0:47}..."
    fi
    
    echo "Proposed commit message: $commit_msg"
    read -p "Commit with this message? [Y/n/e] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ee]$ ]]; then
        read -p "Enter custom message: " custom_msg
        # Truncate custom message if too long
        if [ ${#custom_msg} -gt 40 ]; then
            custom_msg="${custom_msg:0:37}..."
        fi
        commit_msg="$main_type(claude): $custom_msg"
        git commit -m "$commit_msg"
    elif [[ ! $REPLY =~ ^[Nn]$ ]]; then
        git commit -m "$commit_msg"
        echo "Committed: $commit_msg"
    else
        echo "Commit cancelled."
    fi
fi

echo
echo "=== Commit Process Complete ==="
git status
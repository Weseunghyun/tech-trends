#!/usr/bin/env bash
# Common functions and variables for all scripts

# Parse sdd-config.yml and return the specs base directory.
# If obsidian vault_path and project are configured, returns the vault-based path.
# Otherwise returns the traditional $REPO_ROOT/specs path.
get_specs_base_dir() {
    local repo_root="$1"
    local config_file="$repo_root/.specify/sdd-config.yml"

    if [[ -f "$config_file" ]]; then
        # Simple YAML parsing — no external dependencies
        local vault_path base_dir project
        vault_path=$(grep '^  vault_path:' "$config_file" | sed 's/^  vault_path: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' | xargs)
        base_dir=$(grep '^  base_dir:' "$config_file" | sed 's/^  base_dir: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' | xargs)
        project=$(grep '^  project:' "$config_file" | sed 's/^  project: *"\{0,1\}\([^"]*\)"\{0,1\}/\1/' | xargs)

        # Default base_dir to "sdd" if empty
        [[ -z "$base_dir" ]] && base_dir="sdd"

        # Default project to repository directory name if empty
        [[ -z "$project" ]] && project=$(basename "$repo_root")

        # If vault_path is set, use vault-based path
        if [[ -n "$vault_path" ]]; then
            echo "$vault_path/$base_dir/$project"
            return
        fi
    fi

    # Fallback: traditional specs/ directory
    echo "$repo_root/specs"
}

# Get repository root, with fallback for non-git repositories
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        # Fall back to script location for non-git repos
        local script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

# Get current branch, with fallback for non-git repositories
get_current_branch() {
    # First check if SPECIFY_FEATURE environment variable is set
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi

    # Then check git if available
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi

    # For non-git repos, try to find the latest feature directory
    local repo_root=$(get_repo_root)
    local specs_dir=$(get_specs_base_dir "$repo_root")

    if [[ -d "$specs_dir" ]]; then
        local latest_feature=""
        local highest=0

        for dir in "$specs_dir"/*; do
            if [[ -d "$dir" ]]; then
                local dirname=$(basename "$dir")
                if [[ "$dirname" =~ ^([0-9]{3})- ]]; then
                    local number=${BASH_REMATCH[1]}
                    number=$((10#$number))
                    if [[ "$number" -gt "$highest" ]]; then
                        highest=$number
                        latest_feature=$dirname
                    fi
                fi
            fi
        done

        if [[ -n "$latest_feature" ]]; then
            echo "$latest_feature"
            return
        fi
    fi

    echo "main"  # Final fallback
}

# Check if we have git available
has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"

    # For non-git repos, we can't enforce branch naming but still provide output
    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    # Accept both formats:
    #   - feature/<slug>   (standard, e.g. feature/fetch-jp-prices)
    #   - NNN-feature-name (legacy)
    if [[ "$branch" =~ ^feature/ ]] || [[ "$branch" =~ ^[0-9]{3}- ]]; then
        return 0
    fi

    echo "ERROR: Not on a feature branch. Current branch: $branch" >&2
    echo "Feature branches should be named like: feature/<slug> or 001-feature-name" >&2
    return 1
}

get_feature_dir() {
    local specs_dir=$(get_specs_base_dir "$1")
    echo "$specs_dir/$2"
}

# Find feature directory by branch name.
# Supports two strategies:
#   1. .branch file lookup: searches spec dirs for .branch file matching the current git branch
#   2. Numeric prefix: extracts NNN from "NNN-feature-name" branch and finds matching spec dir
find_feature_dir_by_prefix() {
    local repo_root="$1"
    local branch_name="$2"
    local specs_dir=$(get_specs_base_dir "$repo_root")

    # Strategy 1: Search for .branch file matching current git branch
    if [[ -d "$specs_dir" ]]; then
        for dir in "$specs_dir"/*/; do
            if [[ -f "$dir/.branch" ]]; then
                local stored_branch
                stored_branch=$(cat "$dir/.branch" | tr -d '[:space:]')
                if [[ "$stored_branch" == "$branch_name" ]]; then
                    echo "${dir%/}"
                    return
                fi
            fi
        done
    fi

    # Strategy 2: Extract numeric prefix from branch (e.g., "004" from "004-whatever")
    if [[ "$branch_name" =~ ^([0-9]{3})- ]]; then
      local prefix="${BASH_REMATCH[1]}"

      # Search for directories in specs/ that start with this prefix
      local matches=()
      if [[ -d "$specs_dir" ]]; then
          for dir in "$specs_dir"/"$prefix"-*; do
              if [[ -d "$dir" ]]; then
                  matches+=("$(basename "$dir")")
              fi
          done
      fi

    # Handle results
      if [[ ${#matches[@]} -eq 0 ]]; then
          # No match found - return the branch name path (will fail later with clear error)
          echo "$specs_dir/$branch_name"
      elif [[ ${#matches[@]} -eq 1 ]]; then
          # Exactly one match - perfect!
          echo "$specs_dir/${matches[0]}"
      else
          # Multiple matches - this shouldn't happen with proper naming convention
          echo "ERROR: Multiple spec directories found with prefix '$prefix': ${matches[*]}" >&2
          echo "Please ensure only one spec directory exists per numeric prefix." >&2
          echo "$specs_dir/$branch_name"  # Return something to avoid breaking the script
      fi
    fi

    # Fallback: exact match
    echo "$specs_dir/$branch_name"
}

get_feature_paths() {
    local repo_root=$(get_repo_root)
    local current_branch=$(get_current_branch)
    local has_git_repo="false"

    if has_git; then
        has_git_repo="true"
    fi

    # Use prefix-based lookup to support multiple branches per spec
    local feature_dir=$(find_feature_dir_by_prefix "$repo_root" "$current_branch")

    cat <<EOF
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
FEATURE_DIR='$feature_dir'
FEATURE_SPEC='$feature_dir/spec.md'
IMPL_PLAN='$feature_dir/plan.md'
TASKS='$feature_dir/tasks.md'
RESEARCH='$feature_dir/research.md'
DATA_MODEL='$feature_dir/data-model.md'
QUICKSTART='$feature_dir/quickstart.md'
CONTRACTS_DIR='$feature_dir/contracts'
GITLAB_ISSUE_FILE='$feature_dir/.gitlab-issue'
EOF
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }


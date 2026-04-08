#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  🚂 LOCOMETER - Lines of Code Tracker                  ║
# ║  "All aboard the Code Train!"                          ║
# ║                                                          ║
# ║  Fetches all your GitHub repos, clones them, counts    ║
# ║  lines of code, and logs the data for plotting.        ║
# ╚══════════════════════════════════════════════════════════╝

set -euo pipefail

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
GITHUB_USERNAME="vkumar-dev"
DATA_DIR="$(cd "$(dirname "$0")" && pwd)/loc-data"
DATA_FILE="${DATA_DIR}/loc-history.csv"
CLONE_DIR="${DATA_DIR}/repos-temp"
MAX_REPOS=100  # Maximum number of repos to fetch

# ──────────────────────────────────────────────────────────────
# Setup
# ──────────────────────────────────────────────────────────────
mkdir -p "$DATA_DIR"

# Create CSV header if file doesn't exist
if [[ ! -f "$DATA_FILE" ]]; then
    echo "date,total_loc,total_files" > "$DATA_FILE"
fi

# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────
log() {
    echo -e "🚂 \033[1;36m[LOCOMETER]\033[0m $1"
}

error() {
    echo -e "🚂 \033[1;31m[ERROR]\033[0m $1" >&2
}

cleanup() {
    # Remove any leftover temp files (individual repos are deleted after counting)
    if [[ -d "$CLONE_DIR" ]]; then
        rm -rf "$CLONE_DIR"
    fi
}

trap cleanup EXIT

check_dependencies() {
    local deps=("gh" "cloc" "git")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            error "'$dep' is not installed. Please install it first."
            echo "  - gh: https://cli.github.com/"
            echo "  - cloc: https://github.com/AlDanial/cloc"
            echo "  - git: https://git-scm.com/"
            exit 1
        fi
    done
    log "All dependencies found ✓"
}

# ──────────────────────────────────────────────────────────────
# Main Logic
# ──────────────────────────────────────────────────────────────
main() {
    log "╔══════════════════════════════════════════╗"
    log "║  🚂 LOCOMETER - Code Counter Express   ║"
    log "╚══════════════════════════════════════════╝"
    echo ""

    # Check dependencies
    check_dependencies

    # Authenticate with GitHub CLI if needed
    if ! gh auth status &>/dev/null; then
        error "Not authenticated with GitHub CLI."
        log "Please run: gh auth login"
        exit 1
    fi

    # Clean up previous clone directory
    if [[ -d "$CLONE_DIR" ]]; then
        rm -rf "$CLONE_DIR"
    fi
    mkdir -p "$CLONE_DIR"

    # Fetch all repositories (include visibility info)
    log "Fetching repositories for @${GITHUB_USERNAME}..."
    local repos_json
    repos_json=$(gh repo list "$GITHUB_USERNAME" --limit "$MAX_REPOS" --json name,url,isPrivate)

    local repo_count
    repo_count=$(echo "$repos_json" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
    log "Found ${repo_count} repositories"
    echo ""

    # Clone and count
    local total_loc=0
    local total_files=0
    local current=0
    local private_count=0

    while IFS= read -r repo_entry; do
        [[ -z "$repo_entry" ]] && continue

        current=$((current + 1))

        # Parse fields from JSON line
        local repo_url is_private
        repo_url=$(echo "$repo_entry" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['url'])")
        is_private=$(echo "$repo_entry" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d['isPrivate']).lower())")

        local repo_name
        repo_name=$(basename "$repo_url")
        local clone_url="${repo_url}.git"

        if [[ "$is_private" == "true" ]]; then
            private_count=$((private_count + 1))
            log "[${current}/${repo_count}] Cloning 🔒 private repo #${private_count}..."
        else
            log "[${current}/${repo_count}] Cloning ${repo_name}..."
        fi

        # Clone repo (shallow clone for speed)
        if git clone --depth 1 "$clone_url" "${CLONE_DIR}/${repo_name}" &>/dev/null; then
            # Count lines of code using cloc
            local cloc_output
            cloc_output=$(cloc "${CLONE_DIR}/${repo_name}" --json --quiet 2>/dev/null || echo "{}")

            # Parse cloc JSON output
            local repo_loc
            repo_loc=$(echo "$cloc_output" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Sum up 'code' lines from all languages, excluding 'SUM' itself
    total = sum(v.get('code', 0) for k, v in data.items() if k != 'SUM' and k != 'header')
    print(total)
except:
    print(0)
" 2>/dev/null || echo "0")

            local repo_files
            repo_files=$(echo "$cloc_output" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    total = sum(v.get('nFiles', 0) for k, v in data.items() if k != 'SUM' and k != 'header')
    print(int(total))
except:
    print(0)
" 2>/dev/null || echo "0")

            total_loc=$((total_loc + repo_loc))
            total_files=$((total_files + repo_files))

            if [[ "$is_private" == "true" ]]; then
                log "  ↳ 🔒 private | ${repo_loc} LOC | ${repo_files} files"
            else
                log "  ↳ ${repo_loc} LOC | ${repo_files} files"
            fi

            # Delete cloned repo immediately to save disk space
            rm -rf "${CLONE_DIR}/${repo_name}"
        else
            if [[ "$is_private" == "true" ]]; then
                log "  ↳ 🔒 Failed to clone private repo (skipping)"
            else
                log "  ↳ Failed to clone (skipping)"
            fi
        fi
        echo ""
    done < <(echo "$repos_json" | python3 -c "
import sys, json
repos = json.load(sys.stdin)
for r in repos:
    print(json.dumps(r))
")

    # Get current date
    local current_date
    current_date=$(date +"%Y-%m-%d")

    # Remove any existing entry for today (to avoid duplicates on re-runs)
    if [[ -f "$DATA_FILE" ]]; then
        local temp_file
        temp_file=$(mktemp)
        grep -v "^${current_date}," "$DATA_FILE" > "$temp_file" || true
        mv "$temp_file" "$DATA_FILE"
    fi

    # Append to CSV file
    echo "${current_date},${total_loc},${total_files}" >> "$DATA_FILE"

    # Display results
    log "╔══════════════════════════════════════════╗"
    log "║           📊 Today's Results            ║"
    log "╠══════════════════════════════════════════╣"
    printf "║  📅 Date:     %-26s ║\n" "$current_date"
    printf "║  📝 Total LOC: %-24s ║\n" "$total_loc"
    printf "║  📁 Total Files: %-22s ║\n" "$total_files"
    log "╚══════════════════════════════════════════╝"
    echo ""
    log "Data saved to: ${DATA_FILE}"
    log "Run plot_loc.py to generate the visualization!"
}

# ──────────────────────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────────────────────
main "$@"

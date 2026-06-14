#!/usr/bin/env bash

# Wraps everything in main() so a partial curl download doesn't execute anything.
set -euo pipefail

REPO_URL="https://github.com/scrlkx/fc-images-tool"
INSTALL_DIR="${HOME}/.local/share/fc-images-tool"
DESKTOP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="${DESKTOP_DIR}/fc-images-tool.desktop"

main() {
    if [[ "${1:-}" == "--uninstall" ]]; then
        do_uninstall
        return
    fi

    echo "==> fc-images-tool installer"
    echo ""

    check_prerequisites
    clone_or_update
    setup_venv
    install_desktop_shortcut
    print_summary
}

# ── Prerequisites ────────────────────────────────────────────────────────────

check_prerequisites() {
    local ok=true

    if ! command -v git &>/dev/null; then
        echo "ERROR: git is not installed." >&2
        ok=false
    fi

    # Use system python3, not whatever is on PATH (could be a venv)
    local python
    python=$(find_python3) || {
        echo "ERROR: python3 >= 3.10 is required." >&2
        ok=false
    }

    if [[ "$ok" == false ]]; then
        exit 1
    fi

    export PYTHON3="$python"
    echo "  python3: $PYTHON3 ($("$PYTHON3" --version 2>&1))"
}

find_python3() {
    local candidates=("${PYTHON3:-}" /usr/bin/python3 /usr/local/bin/python3 python3)
    for py in "${candidates[@]}"; do
        [[ -z "$py" ]] && continue
        if command -v "$py" &>/dev/null; then
            local ver
            ver=$("$py" -c "import sys; print(sys.version_info[:2])" 2>/dev/null) || continue
            if "$py" -c "import sys; assert sys.version_info >= (3,10)" 2>/dev/null; then
                echo "$py"
                return 0
            fi
        fi
    done
    return 1
}

# ── Clone / Update ───────────────────────────────────────────────────────────

clone_or_update() {
    if [[ -d "${INSTALL_DIR}/.git" ]]; then
        echo "==> Updating existing installation..."
        git -C "$INSTALL_DIR" pull --ff-only
    else
        echo "==> Cloning repository..."
        mkdir -p "$(dirname "$INSTALL_DIR")"
        git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
    fi
}

# ── Venv + Dependencies ──────────────────────────────────────────────────────

setup_venv() {
    local venv="${INSTALL_DIR}/.venv"
    local req="${INSTALL_DIR}/requirements.txt"
    local hash_file="${INSTALL_DIR}/.installed-requirements-hash"

    if [[ ! -d "$venv" ]]; then
        echo "==> Creating virtual environment..."
        "$PYTHON3" -m venv "$venv"
    fi

    local current_hash
    current_hash=$(sha256sum "$req" | cut -d' ' -f1)
    local stored_hash=""
    [[ -f "$hash_file" ]] && stored_hash=$(cat "$hash_file")

    if [[ "$current_hash" != "$stored_hash" ]]; then
        echo "==> Installing Python dependencies (this may take a minute)..."
        "$venv/bin/pip" install --upgrade pip --quiet
        "$venv/bin/pip" install -r "$req"
        echo "$current_hash" > "$hash_file"
    else
        echo "==> Dependencies already up to date."
    fi
}

# ── Desktop shortcut ─────────────────────────────────────────────────────────

install_desktop_shortcut() {
    bash "${INSTALL_DIR}/create-desktop-shortcut.sh" "$INSTALL_DIR"
}

# ── Summary ──────────────────────────────────────────────────────────────────

print_summary() {
    echo ""
    echo "Done!"
    echo ""
    echo "  Open the 'FC Images Tool' shortcut from the GNOME launcher."
    echo "  Or run directly: ${INSTALL_DIR}/run-app.sh"
    echo ""
    echo "NOTE: The first run will download the birefnet-general-lite AI model (~1 GB)."
    echo "      This is a one-time download cached in ~/.u2net/."
}

# ── Uninstall ────────────────────────────────────────────────────────────────

do_uninstall() {
    echo "==> Uninstalling fc-images-tool..."

    [[ -f "$DESKTOP_FILE" ]] && rm -f "$DESKTOP_FILE" && echo "  Removed: ${DESKTOP_FILE}"

    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        echo "  Removed: ${INSTALL_DIR}"
    fi

    echo ""
    echo "Uninstalled."
    echo ""
    echo "NOTE: The AI model cache (~1 GB) was left in place at ~/.u2net/"
    echo "      Remove it manually if you no longer need it:"
    echo "        rm -rf ~/.u2net"
}

main "$@"

#!/bin/bash
set -euo pipefail

# giv CLI Installation Script
# Downloads and installs the appropriate binary for your platform

# Configuration
REPO="fwdslsh/giv"
BINARY_NAME="giv"
DEFAULT_INSTALL_DIR="/usr/local/bin"
USER_INSTALL_DIR="$HOME/.local/bin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
}

# Help message
show_help() {
    cat << EOF
giv CLI Installation Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    -v, --version TAG   Install specific version (default: latest)
    -d, --dir PATH      Installation directory (default: /usr/local/bin or ~/.local/bin)
    -u, --user          Install to user directory (~/.local/bin)
    -f, --force         Force reinstall even if already installed
    --dry-run           Show what would be done without installing

EXAMPLES:
    $0                          # Install latest version to /usr/local/bin
    $0 --user                   # Install to ~/.local/bin (no sudo required)
    $0 --version v1.0.0         # Install specific version
    $0 --dir ~/bin              # Install to custom directory
    $0 --dry-run                # Preview installation

ENVIRONMENT VARIABLES:
    GIV_INSTALL_DIR            Override default installation directory
    GIV_VERSION                Override version to install
    GIV_FORCE                  Force reinstall (set to any value)

EOF
}

# Detect platform and architecture
detect_platform() {
    local os arch
    
    # Detect OS
    case "$(uname -s)" in
        Linux*)     os="linux";;
        Darwin*)    os="darwin";;
        CYGWIN*|MINGW*|MSYS*) os="windows";;
        *)          
            log_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
    
    # Detect architecture
    case "$(uname -m)" in
        x86_64|amd64)   arch="x86_64";;
        arm64|aarch64)  arch="arm64";;
        *)              
            log_error "Unsupported architecture: $(uname -m)"
            exit 1
            ;;
    esac
    
    # Special case for Windows
    if [[ "$os" == "windows" ]]; then
        echo "${os}-${arch}.exe"
    else
        echo "${os}-${arch}"
    fi
}

# Get latest release tag from GitHub
get_latest_version() {
    local api_url="https://api.github.com/repos/${REPO}/releases/latest"
    
    if command -v curl >/dev/null 2>&1; then
        curl -s "$api_url" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/'
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- "$api_url" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/'
    else
        log_error "Neither curl nor wget is available. Please install one of them."
        exit 1
    fi
}

# Check if binary is already installed
check_existing_installation() {
    local install_path="$1"
    
    if [[ -f "$install_path" ]]; then
        local current_version
        if current_version=$("$install_path" --version 2>/dev/null | head -n1); then
            echo "$current_version"
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# Download binary
download_binary() {
    local version="$1"
    local platform="$2"
    local temp_file="$3"
    
    local download_url="https://github.com/${REPO}/releases/download/${version}/giv-${platform}"
    
    log_info "Downloading giv ${version} for ${platform}..."
    log_info "URL: $download_url"
    
    if command -v curl >/dev/null 2>&1; then
        if ! curl -fL --progress-bar "$download_url" -o "$temp_file"; then
            log_error "Failed to download binary"
            return 1
        fi
    elif command -v wget >/dev/null 2>&1; then
        if ! wget --progress=bar:force "$download_url" -O "$temp_file"; then
            log_error "Failed to download binary"
            return 1
        fi
    else
        log_error "Neither curl nor wget is available"
        return 1
    fi
    
    return 0
}

# Install binary
install_binary() {
    local temp_file="$1"
    local install_path="$2"
    local use_sudo="$3"
    
    # Create directory if it doesn't exist
    local install_dir
    install_dir=$(dirname "$install_path")
    
    if [[ ! -d "$install_dir" ]]; then
        log_info "Creating directory: $install_dir"
        if [[ "$use_sudo" == "true" ]]; then
            sudo mkdir -p "$install_dir"
        else
            mkdir -p "$install_dir"
        fi
    fi
    
    # Install binary
    log_info "Installing to: $install_path"
    if [[ "$use_sudo" == "true" ]]; then
        sudo cp "$temp_file" "$install_path"
        sudo chmod +x "$install_path"
    else
        cp "$temp_file" "$install_path"
        chmod +x "$install_path"
    fi
    
    return 0
}

# Verify installation
verify_installation() {
    local install_path="$1"
    
    if [[ ! -f "$install_path" ]]; then
        log_error "Binary not found at $install_path"
        return 1
    fi
    
    if [[ ! -x "$install_path" ]]; then
        log_error "Binary is not executable: $install_path"
        return 1
    fi
    
    local version
    if ! version=$("$install_path" --version 2>/dev/null); then
        log_error "Binary does not execute correctly"
        return 1
    fi
    
    log_success "Installation verified: $version"
    return 0
}

# Add to PATH if needed
check_path() {
    local install_dir="$1"
    
    if [[ ":$PATH:" != *":$install_dir:"* ]]; then
        log_warning "Directory $install_dir is not in your PATH"
        
        local shell_rc
        case "$SHELL" in
            */bash) shell_rc="$HOME/.bashrc";;
            */zsh)  shell_rc="$HOME/.zshrc";;
            */fish) shell_rc="$HOME/.config/fish/config.fish";;
            *)      shell_rc="$HOME/.profile";;
        esac
        
        echo
        log_info "To add it to your PATH, run:"
        echo "    echo 'export PATH=\"$install_dir:\$PATH\"' >> $shell_rc"
        echo "    source $shell_rc"
        echo
        log_info "Or restart your shell"
    fi
}

# Main installation function
main() {
    local version=""
    local install_dir=""
    local force=false
    local dry_run=false
    local user_install=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                version="$2"
                shift 2
                ;;
            -d|--dir)
                install_dir="$2"
                shift 2
                ;;
            -u|--user)
                user_install=true
                shift
                ;;
            -f|--force)
                force=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Check environment variables
    if [[ -n "${GIV_VERSION:-}" ]]; then
        version="$GIV_VERSION"
    fi
    
    if [[ -n "${GIV_INSTALL_DIR:-}" ]]; then
        install_dir="$GIV_INSTALL_DIR"
    fi
    
    if [[ -n "${GIV_FORCE:-}" ]]; then
        force=true
    fi
    
    # Determine installation directory
    if [[ -z "$install_dir" ]]; then
        if [[ "$user_install" == "true" ]]; then
            install_dir="$USER_INSTALL_DIR"
        else
            install_dir="$DEFAULT_INSTALL_DIR"
        fi
    fi
    
    local install_path="$install_dir/$BINARY_NAME"
    local use_sudo=false
    
    # Check if we need sudo
    if [[ ! -w "$install_dir" ]] && [[ "$install_dir" != "$USER_INSTALL_DIR"* ]]; then
        use_sudo=true
        log_info "Installation to $install_dir requires sudo privileges"
    fi
    
    # Detect platform
    local platform
    platform=$(detect_platform)
    log_info "Detected platform: $platform"
    
    # Get version
    if [[ -z "$version" ]]; then
        log_info "Getting latest release version..."
        version=$(get_latest_version)
        if [[ -z "$version" ]]; then
            log_error "Failed to get latest version"
            exit 1
        fi
    fi
    
    log_info "Installing giv version: $version"
    
    # Check existing installation
    if [[ "$force" == "false" ]]; then
        local current_version
        if current_version=$(check_existing_installation "$install_path"); then
            log_info "Found existing installation: $current_version"
            if [[ "$current_version" == *"$version"* ]]; then
                log_success "giv $version is already installed at $install_path"
                exit 0
            else
                log_info "Upgrading from $current_version to $version"
            fi
        fi
    fi
    
    if [[ "$dry_run" == "true" ]]; then
        echo
        log_info "DRY RUN - Would perform the following actions:"
        echo "  • Download: giv-$platform from $version"
        echo "  • Install to: $install_path"
        echo "  • Use sudo: $use_sudo"
        echo "  • Platform: $platform"
        exit 0
    fi
    
    # Create temporary file
    local temp_file
    temp_file=$(mktemp)
    trap "rm -f '$temp_file'" EXIT
    
    # Download binary
    if ! download_binary "$version" "$platform" "$temp_file"; then
        exit 1
    fi
    
    # Install binary
    if ! install_binary "$temp_file" "$install_path" "$use_sudo"; then
        exit 1
    fi
    
    # Verify installation
    if ! verify_installation "$install_path"; then
        exit 1
    fi
    
    # Check PATH
    check_path "$install_dir"
    
    echo
    log_success "giv has been installed successfully!"
    log_info "Run 'giv --help' to get started"
    
    # Show quick start
    echo
    echo "Quick start:"
    echo "  giv init                    # Initialize giv in your project"
    echo "  giv config set api.key KEY  # Set your API key"
    echo "  giv message --dry-run       # Test without API call"
}

# Run main function
main "$@"
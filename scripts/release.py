#!/usr/bin/env python3
"""
Release automation script for TeamSpeak MCP
Usage: python scripts/release.py [patch|minor|major]
"""

import re
import subprocess
import sys
from pathlib import Path

def get_current_version():
    """Get current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)

def bump_version(version, bump_type):
    """Bump version according to semantic versioning"""
    parts = list(map(int, version.split('.')))
    
    if bump_type == "patch":
        parts[2] += 1
    elif bump_type == "minor":
        parts[1] += 1
        parts[2] = 0
    elif bump_type == "major":
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return ".".join(map(str, parts))

def update_version_in_file(file_path, old_version, new_version):
    """Update version in a file"""
    content = Path(file_path).read_text()
    updated = content.replace(f'version = "{old_version}"', f'version = "{new_version}"')
    Path(file_path).write_text(updated)

def run_command(cmd):
    """Run shell command and return result"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ["patch", "minor", "major"]:
        print("Usage: python scripts/release.py [patch|minor|major]")
        print("Examples:")
        print("  python scripts/release.py patch   # 1.0.3 -> 1.0.4")
        print("  python scripts/release.py minor   # 1.0.3 -> 1.1.0")
        print("  python scripts/release.py major   # 1.0.3 -> 2.0.0")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    
    # Check git status
    status = run_command("git status --porcelain")
    if status:
        print("❌ Git working directory is not clean. Commit your changes first.")
        sys.exit(1)
    
    # Get current version and bump it
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)
    
    print(f"🚀 Releasing TeamSpeak MCP")
    print(f"📋 Current version: {current_version}")
    print(f"📋 New version: {new_version}")
    print(f"📋 Bump type: {bump_type}")
    
    # Confirm
    response = input("\n❓ Continue with release? (y/N): ")
    if response.lower() != 'y':
        print("❌ Release cancelled")
        sys.exit(0)
    
    # Update version in pyproject.toml
    print("📝 Updating version in pyproject.toml...")
    update_version_in_file("pyproject.toml", current_version, new_version)
    
    # Update version in __init__.py if it exists
    init_file = Path("teamspeak_mcp/__init__.py")
    if init_file.exists():
        print("📝 Updating version in __init__.py...")
        content = init_file.read_text()
        updated = content.replace(f'__version__ = "{current_version}"', f'__version__ = "{new_version}"')
        init_file.write_text(updated)
    
    # Commit changes
    print("📝 Committing version bump...")
    run_command("git add -A")
    run_command(f'git commit -m "Bump version to {new_version}"')
    
    # Create and push tag
    print("🏷️ Creating and pushing tag...")
    tag_name = f"v{new_version}"
    run_command(f"git tag {tag_name}")
    run_command("git push origin main")
    run_command(f"git push origin {tag_name}")
    
    print(f"")
    print(f"🎉 Release initiated!")
    print(f"🔗 Tag: {tag_name}")
    print(f"🤖 GitHub Actions will now:")
    print(f"   1. Build the package")
    print(f"   2. Test on TestPyPI")  
    print(f"   3. Publish to PyPI")
    print(f"   4. Build Docker images")
    print(f"   5. Create GitHub release")
    print(f"")
    print(f"🔍 Monitor progress:")
    print(f"   - Actions: https://github.com/MarlBurroW/teamspeak-mcp/actions")
    print(f"   - PyPI: https://pypi.org/project/teamspeak-mcp/{new_version}/")
    print(f"   - Docker: ghcr.io/marlburrow/teamspeak-mcp:{tag_name}")

if __name__ == "__main__":
    main() 
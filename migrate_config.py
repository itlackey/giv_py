#!/usr/bin/env python3
"""
Configuration migration utility for transitioning from Bash to Python giv.

This utility helps users migrate their existing Bash giv configuration 
to work with the Python implementation.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ConfigMigrator:
    """Handles migration of giv configuration from Bash to Python."""
    
    def __init__(self):
        self.home_config = Path.home() / ".giv" / "config"
        self.bash_templates = Path.home() / ".giv" / "templates"
        self.issues = []
        self.migrated_items = []
    
    def find_bash_installations(self) -> List[Path]:
        """Find existing Bash giv installations."""
        possible_locations = [
            Path("/usr/local/bin/giv"),
            Path("/usr/bin/giv"),
            Path.home() / ".local/bin/giv",
            Path.home() / "bin/giv",
        ]
        
        bash_installations = []
        for location in possible_locations:
            if location.exists():
                try:
                    # Check if it's a bash script
                    with open(location, 'r') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith('#!/bin/bash') or first_line.startswith('#!/usr/bin/env bash'):
                            bash_installations.append(location)
                except (PermissionError, UnicodeDecodeError):
                    continue
        
        return bash_installations
    
    def analyze_config(self) -> Tuple[bool, Dict[str, str]]:
        """Analyze existing configuration for compatibility."""
        if not self.home_config.exists():
            return True, {}
        
        config_data = {}
        compatible = True
        
        try:
            with open(self.home_config, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' not in line:
                        self.issues.append(f"Line {line_num}: Invalid format (missing '='): {line}")
                        compatible = False
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    config_data[key] = value
                    
                    # Check for deprecated or changed keys
                    if key == 'api_url':
                        self.issues.append(f"Line {line_num}: 'api_url' should be 'api.url'")
                        compatible = False
                    elif key == 'api_key':
                        self.issues.append(f"Line {line_num}: 'api_key' should be 'api.key'")
                        compatible = False
        
        except Exception as e:
            self.issues.append(f"Error reading config file: {e}")
            compatible = False
        
        return compatible, config_data
    
    def migrate_config(self, config_data: Dict[str, str], backup: bool = True) -> bool:
        """Migrate configuration to Python-compatible format."""
        if backup and self.home_config.exists():
            backup_path = self.home_config.with_suffix('.config.bash-backup')
            shutil.copy2(self.home_config, backup_path)
            self.migrated_items.append(f"Backed up config to {backup_path}")
        
        # Migrate key names
        migrations = {
            'api_url': 'api.url',
            'api_key': 'api.key',
            'api_model': 'api.model',
            'output_mode': 'output.mode',
            'output_file': 'output.file',
        }
        
        migrated_config = {}
        for key, value in config_data.items():
            new_key = migrations.get(key, key)
            migrated_config[new_key] = value
            if new_key != key:
                self.migrated_items.append(f"Migrated '{key}' to '{new_key}'")
        
        # Write migrated config
        try:
            self.home_config.parent.mkdir(parents=True, exist_ok=True)
            with open(self.home_config, 'w') as f:
                for key, value in sorted(migrated_config.items()):
                    f.write(f"{key}={value}\n")
            
            self.migrated_items.append(f"Updated config file: {self.home_config}")
            return True
        
        except Exception as e:
            self.issues.append(f"Error writing config file: {e}")
            return False
    
    def migrate_templates(self, backup: bool = True) -> bool:
        """Migrate custom templates if they exist."""
        if not self.bash_templates.exists():
            return True  # No templates to migrate, that's fine
        
        python_giv_dir = Path(__file__).parent.parent  # Assuming script is in giv_py/
        python_templates = python_giv_dir / "giv_cli" / "templates"
        
        if not python_templates.exists():
            self.issues.append(f"Python templates directory not found: {python_templates}")
            return False
        
        try:
            for template_file in self.bash_templates.glob("*.md"):
                python_template = python_templates / template_file.name
                
                if backup and python_template.exists():
                    backup_path = python_template.with_suffix('.md.default-backup')
                    shutil.copy2(python_template, backup_path)
                    self.migrated_items.append(f"Backed up default template to {backup_path}")
                
                shutil.copy2(template_file, python_template)
                self.migrated_items.append(f"Migrated template: {template_file.name}")
            
            return True
        
        except Exception as e:
            self.issues.append(f"Error migrating templates: {e}")
            return False
    
    def validate_python_installation(self) -> bool:
        """Validate that Python giv is properly installed."""
        try:
            import subprocess
            result = subprocess.run(['giv', '--version'], capture_output=True, text=True)
            if result.returncode == 0 and 'python' in result.stdout.lower():
                self.migrated_items.append("✅ Python giv installation validated")
                return True
            else:
                self.issues.append("Python giv not found or not working")
                return False
        except Exception as e:
            self.issues.append(f"Error validating Python installation: {e}")
            return False
    
    def create_test_config(self) -> bool:
        """Create a minimal test configuration."""
        test_config = {
            'api.url': 'https://api.openai.com/v1/chat/completions',
            'api.model': 'gpt-4',
            'output.mode': 'auto',
        }
        
        try:
            self.home_config.parent.mkdir(parents=True, exist_ok=True)
            with open(self.home_config, 'w') as f:
                f.write("# Migrated configuration for Python giv\n")
                f.write("# Set your API key with: giv config set api.key YOUR_KEY\n\n")
                for key, value in test_config.items():
                    f.write(f"{key}={value}\n")
            
            self.migrated_items.append(f"Created test configuration: {self.home_config}")
            return True
        
        except Exception as e:
            self.issues.append(f"Error creating test configuration: {e}")
            return False


def print_status(title: str, items: List[str], symbol: str = "•"):
    """Print a formatted status section."""
    if not items:
        return
    
    print(f"\n{title}:")
    for item in items:
        print(f"  {symbol} {item}")


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate giv configuration from Bash to Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check                    # Check current configuration
  %(prog)s migrate                  # Perform migration with backups
  %(prog)s migrate --no-backup      # Migrate without creating backups
  %(prog)s create-test              # Create minimal test configuration
        """
    )
    
    parser.add_argument(
        'action',
        choices=['check', 'migrate', 'create-test'],
        help='Action to perform'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup files'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force migration even if issues are detected'
    )
    
    args = parser.parse_args()
    
    migrator = ConfigMigrator()
    
    print("🔄 giv Configuration Migration Utility")
    print("=" * 40)
    
    if args.action == 'check':
        print("🔍 Analyzing current configuration...")
        
        # Find Bash installations
        bash_installs = migrator.find_bash_installations()
        if bash_installs:
            print(f"\n📍 Found Bash giv installations:")
            for install in bash_installs:
                print(f"  • {install}")
        else:
            print("\n📍 No Bash giv installations found")
        
        # Analyze configuration
        compatible, config_data = migrator.analyze_config()
        
        if config_data:
            print(f"\n⚙️ Current configuration ({migrator.home_config}):")
            for key, value in config_data.items():
                # Hide sensitive values
                display_value = value if 'key' not in key.lower() else '***'
                print(f"  • {key} = {display_value}")
        else:
            print(f"\n⚙️ No configuration found at {migrator.home_config}")
        
        # Check Python installation
        python_working = migrator.validate_python_installation()
        
        print_status("✅ Migration Status", migrator.migrated_items, "✅")
        print_status("⚠️ Issues Found", migrator.issues, "⚠️")
        
        if compatible and python_working:
            print(f"\n🎉 Configuration is ready for Python giv!")
        elif not migrator.issues:
            print(f"\n📝 No configuration found - you can create one with 'create-test'")
        else:
            print(f"\n🚨 Issues need to be resolved before migration")
    
    elif args.action == 'migrate':
        print("🔄 Starting configuration migration...")
        
        compatible, config_data = migrator.analyze_config()
        
        if migrator.issues and not args.force:
            print_status("⚠️ Issues that need attention", migrator.issues, "⚠️")
            print("\n❌ Migration aborted due to issues.")
            print("   Use --force to migrate anyway, or fix issues first.")
            sys.exit(1)
        
        success = True
        
        if config_data:
            if not migrator.migrate_config(config_data, backup=not args.no_backup):
                success = False
        
        if not migrator.migrate_templates(backup=not args.no_backup):
            success = False
        
        if not migrator.validate_python_installation():
            success = False
        
        print_status("✅ Migration completed", migrator.migrated_items, "✅")
        print_status("⚠️ Issues encountered", migrator.issues, "⚠️")
        
        if success:
            print(f"\n🎉 Migration completed successfully!")
            print(f"   You can now use the Python version of giv.")
            print(f"   Test with: giv config list")
        else:
            print(f"\n❌ Migration completed with issues.")
            sys.exit(1)
    
    elif args.action == 'create-test':
        print("📝 Creating test configuration...")
        
        if migrator.home_config.exists() and not args.force:
            print(f"❌ Configuration already exists at {migrator.home_config}")
            print("   Use --force to overwrite")
            sys.exit(1)
        
        if migrator.create_test_config():
            print(f"✅ Test configuration created at {migrator.home_config}")
            print(f"   Set your API key with: giv config set api.key YOUR_KEY")
            print(f"   Test with: giv message --dry-run")
        else:
            print_status("❌ Errors", migrator.issues, "❌")
            sys.exit(1)


if __name__ == '__main__':
    main()

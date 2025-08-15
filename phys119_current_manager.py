#!/usr/bin/env python3
"""
PHYS119 Current Branch Manager for Lab Content Distribution
Uses a single "current" branch that gets updated each week
Compatible with Windows, macOS, and Linux
Updated for branch_test repo and lab/tree URL format
"""

import subprocess
import sys
import os
from datetime import datetime
import json
import platform

class PHYS119CurrentBranchManager:
    def __init__(self, config_file='phys119_current_config.json'):
        """Initialize with PHYS119 configuration"""
        self.config = self.load_config(config_file)
        self.total_labs = self.config.get('total_labs', 11)  # Labs 0-10
        self.repo_url = self.config.get('repo_url', 'https://github.com/phys119/branch_test')
        self.hub_url = self.config.get('hub_url', 'https://phys119.phas.ubc.ca')
        self.repo_name = self.config.get('repo_name', 'branch_test')
        self.current_branch = self.config.get('current_branch', 'current-labs')
        self.lab_names = self.config.get('lab_names', {})
        self.is_windows = platform.system() == 'Windows'
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def run_command(self, cmd):
        """Run shell command and return output"""
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            # Only print errors for commands we expect to succeed
            if not ("branch -D" in cmd or "push origin --delete" in cmd):
                print(f"Error running command: {cmd}")
                print(f"Error message: {result.stderr}")
        return result
    
    def safe_delete_branch(self, branch_name, location='both'):
        """Safely attempt to delete a branch (local, remote, or both)"""
        if location in ['local', 'both']:
            # Try to delete local branch
            result = subprocess.run(
                f"git branch -D {branch_name}", 
                capture_output=True, 
                text=True, 
                shell=True
            )
            if result.returncode == 0:
                print(f"  Deleted existing local branch: {branch_name}")
        
        if location in ['remote', 'both']:
            # Try to delete remote branch
            result = subprocess.run(
                f"git push origin --delete {branch_name}", 
                capture_output=True, 
                text=True, 
                shell=True
            )
            if result.returncode == 0:
                print(f"  Deleted existing remote branch: {branch_name}")
    
    def initialize_current_branch(self):
        """Initialize the current branch with Lab00 only"""
        print(f"\nInitializing {self.current_branch} branch with Lab00 only")
        
        # Ensure we're on main and up to date
        self.run_command("git checkout main")
        self.run_command("git pull origin main")
        
        # Clean up any existing current branch
        self.safe_delete_branch(self.current_branch, 'both')
        
        # Create new current branch
        self.run_command(f"git checkout -b {self.current_branch}")
        
        # Remove all labs except Lab00
        labs_to_remove = []
        for lab_num in range(1, self.total_labs):
            lab_dir = f"Lab{lab_num:02d}"
            if os.path.exists(lab_dir):
                labs_to_remove.append(lab_dir)
        
        if labs_to_remove:
            for lab_dir in labs_to_remove:
                self.run_command(f"git rm -rf {lab_dir}")
            
            # Commit changes
            self.run_command('git commit -m "Initialize current branch: Lab 0 only"')
        else:
            print(f"  No future labs to remove")
        
        # Push to remote
        self.run_command(f"git push -u origin {self.current_branch}")
        print(f"✓ Branch {self.current_branch} initialized with Lab00 only")
        
        return self.current_branch
    
    def update_current_week(self, target_lab):
        """Update current branch to include labs 0 through target_lab"""
        print(f"\n{'='*50}")
        print(f" Updating {self.current_branch} to include Lab {target_lab}")
        print(f" Including Labs 0-{target_lab}")
        print(f"{'='*50}")
        
        # Ensure we're on the current branch
        self.run_command(f"git checkout {self.current_branch}")
        self.run_command(f"git pull origin {self.current_branch}")
        
        # Check what labs currently exist in the branch
        current_labs = []
        for lab_num in range(self.total_labs):
            lab_dir = f"Lab{lab_num:02d}"
            if os.path.exists(lab_dir):
                current_labs.append(lab_num)
        
        print(f"Current labs in branch: {current_labs}")
        print(f"Target: Labs 0-{target_lab}")
        
        # Determine what needs to be added or removed
        target_labs = list(range(target_lab + 1))
        labs_to_add = [lab for lab in target_labs if lab not in current_labs]
        labs_to_remove = [lab for lab in current_labs if lab not in target_labs]
        
        changes_made = False
        
        # Remove future labs that shouldn't be there yet
        if labs_to_remove:
            print(f"\nRemoving labs: {labs_to_remove}")
            for lab_num in labs_to_remove:
                lab_dir = f"Lab{lab_num:02d}"
                self.run_command(f"git rm -rf {lab_dir}")
                changes_made = True
        
        # Add new labs from main branch
        if labs_to_add:
            print(f"\nAdding labs: {labs_to_add}")
            for lab_num in labs_to_add:
                lab_dir = f"Lab{lab_num:02d}"
                # Check if lab exists in main branch
                result = self.run_command(f"git show main:{lab_dir}/")
                if result.returncode == 0:  # Lab exists in main
                    self.run_command(f"git checkout main -- {lab_dir}")
                    changes_made = True
                    print(f"  Added {lab_dir}")
                else:
                    print(f"  Warning: {lab_dir} not found in main branch")
        
        # Commit and push changes if any were made
        if changes_made:
            commit_message = f"Updated to include Labs 0-{target_lab}"
            self.run_command(f'git add .')
            self.run_command(f'git commit -m "{commit_message}"')
            self.run_command(f'git push origin {self.current_branch}')
            print(f"\n✓ {self.current_branch} updated successfully!")
        else:
            print(f"\n✓ {self.current_branch} already up to date")
        
        # Generate links for current state
        self.show_current_links()
        
        return self.current_branch
    
    def show_current_links(self):
        """Show nbgitpuller links for current branch state"""
        print(f"\n{'='*60}")
        print(f" Current nbgitpuller Links ({self.current_branch} branch)")
        print(f"{'='*60}")
        
        # Base link for the repository
        base_link = (
            f"{self.hub_url}/hub/user-redirect/git-pull"
            f"?repo={self.repo_url}"
            f"&branch={self.current_branch}"
            f"&urlpath=lab/tree/{self.repo_name}"
        )
        
        print(f"\nRepository Root:")
        print(f"{base_link}")
        
        # Check what labs are currently available
        available_labs = []
        for lab_num in range(self.total_labs):
            lab_dir = f"Lab{lab_num:02d}"
            if os.path.exists(lab_dir):
                available_labs.append(lab_num)
        
        if available_labs:
            print(f"\nAvailable Lab Links:")
            print("=" * 40)
            
            for lab_num in available_labs:
                lab_name = self.lab_names.get(str(lab_num), f"Lab {lab_num}")
                lab_dir = f"Lab{lab_num:02d}"
                
                # Main lab notebook link
                notebook_link = (
                    f"{self.hub_url}/hub/user-redirect/git-pull"
                    f"?repo={self.repo_url}"
                    f"&branch={self.current_branch}"
                    f"&urlpath=lab/tree/{self.repo_name}/{lab_dir}/Lab{lab_num:02d}.ipynb"
                )
                
                # Lab folder link
                folder_link = (
                    f"{self.hub_url}/hub/user-redirect/git-pull"
                    f"?repo={self.repo_url}"
                    f"&branch={self.current_branch}"
                    f"&urlpath=lab/tree/{self.repo_name}/{lab_dir}"
                )
                
                print(f"\nLab {lab_num}: {lab_name}")
                print(f"Notebook: {notebook_link}")
                print(f"Folder:   {folder_link}")
        
        print(f"\n{'='*60}")
        print("💡 Tip: These links will always point to the current week's content!")
        print("💡 You only need to update Canvas once with these links.")
    
    def get_status(self):
        """Show current branch status and available labs"""
        print(f"\n{'='*50}")
        print(f" Current Branch Status")
        print(f"{'='*50}")
        
        # Check if current branch exists
        result = self.run_command(f"git show-ref --verify --quiet refs/heads/{self.current_branch}")
        if result.returncode != 0:
            print(f"❌ Branch '{self.current_branch}' does not exist locally")
            print("Run 'python script.py init' to create it")
            return
        
        # Switch to current branch and check status
        self.run_command(f"git checkout {self.current_branch}")
        
        # Show current labs
        available_labs = []
        for lab_num in range(self.total_labs):
            lab_dir = f"Lab{lab_num:02d}"
            if os.path.exists(lab_dir):
                available_labs.append(lab_num)
        
        if available_labs:
            max_lab = max(available_labs)
            print(f"✓ Branch: {self.current_branch}")
            print(f"✓ Current Lab Range: 0-{max_lab}")
            print(f"✓ Available Labs: {available_labs}")
            print(f"✓ Latest Lab: Lab{max_lab:02d}")
        else:
            print(f"⚠️  No labs found in {self.current_branch}")
        
        # Check if remote branch exists
        result = self.run_command(f"git ls-remote --heads origin {self.current_branch}")
        if result.stdout.strip():
            print(f"✓ Remote branch exists")
        else:
            print(f"❌ Remote branch does not exist")

def main():
    """Main execution function"""
    if len(sys.argv) < 2:
        print("""
PHYS119 Current Branch Manager - Single Updating Branch
=======================================================

Usage: python phys119_current_manager.py <command> [options]

Commands:
  setup                   Initial setup wizard
  init                    Initialize current branch (Lab00 only)
  update <lab_number>     Update current branch to include Labs 0-<lab_number>
  status                  Show current branch status and links
  links                   Show current nbgitpuller links
  
Examples:
  python phys119_current_manager.py setup     # First-time setup
  python phys119_current_manager.py init      # Create current branch with Lab00
  python phys119_current_manager.py update 0  # Labs 0 only (Lab00)
  python phys119_current_manager.py update 1  # Labs 0-1 (Lab00, Lab01)
  python phys119_current_manager.py update 2  # Labs 0-2 (Lab00, Lab01, Lab02)
  python phys119_current_manager.py status    # Check current status
  python phys119_current_manager.py links     # Show current links
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    manager = PHYS119CurrentBranchManager()
    
    if command == 'init':
        manager.initialize_current_branch()
        manager.show_current_links()
    
    elif command == 'update':
        if len(sys.argv) < 3:
            print("Error: Please specify lab number (0-10)")
            print("Example: python phys119_current_manager.py update 2")
            sys.exit(1)
        
        try:
            target_lab = int(sys.argv[2])
            if target_lab < 0 or target_lab > 10:
                print("Error: Lab number must be between 0 and 10")
                sys.exit(1)
        except ValueError:
            print("Error: Lab number must be an integer")
            sys.exit(1)
        
        manager.update_current_week(target_lab)
    
    elif command == 'status':
        manager.get_status()
        manager.show_current_links()
    
    elif command == 'links':
        manager.show_current_links()
    
    elif command == 'setup':
        print("\n" + "="*50)
        print(" PHYS119 Current Branch Manager Setup")
        print("="*50)
        
        config = {}
        config['total_labs'] = 11  # Labs 0-10
        
        print("\nRepository URL")
        repo_input = input("Enter repo URL [https://github.com/phys119/branch_test]: ").strip()
        config['repo_url'] = repo_input if repo_input else "https://github.com/phys119/branch_test"
        
        print("\nRepository Name (for URL paths)")
        repo_name_input = input("Enter repo name [branch_test]: ").strip()
        config['repo_name'] = repo_name_input if repo_name_input else "branch_test"
        
        print("\nJupyterHub URL")
        hub_input = input("Enter hub URL [https://phys119.phas.ubc.ca]: ").strip()
        config['hub_url'] = hub_input if hub_input else "https://phys119.phas.ubc.ca"
        
        print("\nCurrent Branch Name")
        branch_input = input("Enter branch name [current-labs]: ").strip()
        config['current_branch'] = branch_input if branch_input else "current-labs"
        
        # Lab names for PHYS119
        config['lab_names'] = {
            "0": "Introduction to Experimentation",
            "1": "Hooke's Law",
            "2": "Pendulum",
            "3": "Hair Diameter",
            "4": "Photoelectric Effect",
            "5": "Ideal Gas Law",
            "6": "Light Intensity",
            "7": "Radioactivity",
            "8": "Electron Diffraction", 
            "9": "Spectroscopy",
            "10": "Final Project"
        }
        
        with open('phys119_current_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\n✓ Configuration saved to phys119_current_config.json")
        print("\nNext steps:")
        print("1. Run: python phys119_current_manager.py init")
        print("   (This will create the current branch with Lab00)")
        print("2. Run: python phys119_current_manager.py links")
        print("   (Get the nbgitpuller links for Canvas)")
        print("3. Each week, run: python phys119_current_manager.py update <lab_number>")
        print("   - update 0: Lab 0 only")
        print("   - update 1: Labs 0-1") 
        print("   - update 2: Labs 0-2, etc.")
    
    else:
        print(f"Unknown command: {command}")
        print("Run 'python phys119_current_manager.py' for usage information")
        sys.exit(1)

if __name__ == "__main__":
    main()
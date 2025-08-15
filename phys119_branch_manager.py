#!/usr/bin/env python3
"""
PHYS119 Branch Manager for Lab Content Distribution
Automatically creates and updates branches for selective lab release
Compatible with Windows, macOS, and Linux
"""

import subprocess
import sys
import os
from datetime import datetime
import json
import platform

class PHYS119BranchManager:
    def __init__(self, config_file='phys119_config.json'):
        """Initialize with PHYS119 configuration"""
        self.config = self.load_config(config_file)
        self.total_labs = self.config.get('total_labs', 11)  # Labs 0-10
        self.repo_url = self.config.get('repo_url', '')
        self.hub_url = self.config.get('hub_url', '')
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
        if result.returncode != 0 and "error" not in cmd.lower():
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
    
    def create_lab_branch(self, lab_num, cumulative=True):
        """Create a branch with content for specific lab(s)"""
        if cumulative:
            branch_name = f"deploy-labs00-{lab_num:02d}"
            commit_msg = f"Labs 0-{lab_num} content"
        else:
            branch_name = f"deploy-lab{lab_num:02d}"
            commit_msg = f"Lab {lab_num} only"
        
        print(f"\nCreating branch: {branch_name}")
        
        # Ensure we're on main and up to date
        self.run_command("git checkout main")
        self.run_command("git pull origin main")
        
        # Clean up any existing branches
        self.safe_delete_branch(branch_name, 'both')
        
        # Create new branch
        self.run_command(f"git checkout -b {branch_name}")
        
        # Remove future labs
        labs_to_remove = []
        for future_lab in range(lab_num + 1, self.total_labs):
            lab_dir = f"Lab{future_lab:02d}"
            if os.path.exists(lab_dir):
                labs_to_remove.append(lab_dir)
        
        # Remove non-cumulative labs if needed
        if not cumulative:
            for past_lab in range(0, lab_num):
                lab_dir = f"Lab{past_lab:02d}"
                if os.path.exists(lab_dir):
                    labs_to_remove.append(lab_dir)
        
        if labs_to_remove:
            for lab_dir in labs_to_remove:
                self.run_command(f"git rm -rf {lab_dir}")
            
            # Commit changes
            self.run_command(f'git commit -m "{commit_msg}"')
        else:
            print(f"  No changes needed for {branch_name}")
        
        # Push to remote
        self.run_command(f"git push -f origin {branch_name}")
        print(f"✓ Branch {branch_name} created and pushed")
        
        return branch_name
    
    def update_all_branches(self, current_lab):
        """Update all branches up to current lab"""
        print(f"\n{'='*50}")
        print(f" Updating branches for Lab {current_lab}")
        print(f"{'='*50}")
        
        branches_created = []
        
        # Create cumulative branches
        for lab in range(current_lab + 1):
            branch = self.create_lab_branch(lab, cumulative=True)
            branches_created.append(branch)
        
        # Optional: Create individual lab branches
        if self.config.get('create_individual_branches', False):
            print(f"\n{'='*50}")
            print(f" Creating individual lab branches")
            print(f"{'='*50}")
            for lab in range(current_lab + 1):
                branch = self.create_lab_branch(lab, cumulative=False)
                branches_created.append(branch)
        
        # Return to main branch
        self.run_command("git checkout main")
        
        print(f"\n{'='*50}")
        print(f"✓ Successfully created/updated {len(branches_created)} branches")
        print(f"{'='*50}")
        return branches_created
    
    def generate_nbgitpuller_links(self, lab_num):
        """Generate nbgitpuller links for a specific lab"""
        if not self.repo_url or not self.hub_url:
            print("Warning: repo_url and hub_url must be set in config to generate links")
            return []
        
        links = []
        branch_name = f"deploy-labs00-{lab_num:02d}"
        lab_folder = f"Lab{lab_num:02d}"
        lab_name = self.lab_names.get(str(lab_num), f"Lab {lab_num}")
        
        # Link to prelab notebook
        prelab_link = (
            f"{self.hub_url}/hub/user-redirect/git-pull"
            f"?repo={self.repo_url}"
            f"&branch={branch_name}"
            f"&urlpath=tree/{lab_folder}/prelab{lab_num:02d}.ipynb"
        )
        
        # Link to main lab notebook
        notebook_link = (
            f"{self.hub_url}/hub/user-redirect/git-pull"
            f"?repo={self.repo_url}"
            f"&branch={branch_name}"
            f"&urlpath=tree/{lab_folder}/Lab{lab_num:02d}.ipynb"
        )
        
        # Link to lab folder
        folder_link = (
            f"{self.hub_url}/hub/user-redirect/git-pull"
            f"?repo={self.repo_url}"
            f"&branch={branch_name}"
            f"&urlpath=tree/{lab_folder}"
        )
        
        links.append({
            'lab': lab_num,
            'name': lab_name,
            'branch': branch_name,
            'folder_link': folder_link,
            'prelab_link': prelab_link,
            'notebook_link': notebook_link
        })
        
        return links

def main():
    """Main execution function"""
    if len(sys.argv) < 2:
        print("""
PHYS119 Branch Manager - Selective Lab Content Distribution
===========================================================

Usage: python phys119_branch_manager.py <command> [options]

Commands:
  setup                   Initial setup wizard
  update <lab_number>     Update branches for specified lab (0-10)
  links <lab_number>      Generate nbgitpuller links for specified lab
  status                  Show current branch status
  
Examples:
  python phys119_branch_manager.py setup       # First-time setup
  python phys119_branch_manager.py update 2    # Release labs 0-2
  python phys119_branch_manager.py links 2     # Get links for lab 2
  python phys119_branch_manager.py status      # Check current branches
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    manager = PHYS119BranchManager()
    
    if command == 'update':
        if len(sys.argv) < 3:
            print("Error: Please specify lab number (0-10)")
            print("Example: python phys119_branch_manager.py update 2")
            sys.exit(1)
        
        try:
            lab = int(sys.argv[2])
            if lab < 0 or lab > 10:
                print("Error: Lab number must be between 0 and 10")
                sys.exit(1)
        except ValueError:
            print("Error: Lab number must be an integer")
            sys.exit(1)
        
        manager.update_all_branches(lab)
        
        # Generate links for the new lab
        links = manager.generate_nbgitpuller_links(lab)
        if links:
            print(f"\n{'='*50}")
            print(f" nbgitpuller Links for Lab {lab}")
            print(f"{'='*50}")
            for link_info in links:
                print(f"\nLab {link_info['lab']}: {link_info['name']}")
                print(f"{'='*40}")
                print(f"Prelab:   {link_info['prelab_link']}")
                print(f"\nNotebook: {link_info['notebook_link']}")
                print(f"\nFolder:   {link_info['folder_link']}")
    
    elif command == 'links':
        if len(sys.argv) < 3:
            print("Error: Please specify lab number")
            sys.exit(1)
        
        try:
            lab = int(sys.argv[2])
        except ValueError:
            print("Error: Lab number must be an integer")
            sys.exit(1)
            
        links = manager.generate_nbgitpuller_links(lab)
        for link_info in links:
            print(f"\n{'='*50}")
            print(f" Lab {link_info['lab']}: {link_info['name']}")
            print(f"{'='*50}")
            print(f"\nPrelab:   {link_info['prelab_link']}")
            print(f"\nNotebook: {link_info['notebook_link']}")
            print(f"\nFolder:   {link_info['folder_link']}")
    
    elif command == 'status':
        print("\nChecking branch status...")
        print("=" * 50)
        
        # Show local branches
        result = subprocess.run("git branch", capture_output=True, text=True, shell=True)
        print("\nLocal branches:")
        print(result.stdout)
        
        # Show remote branches that match our pattern
        result = subprocess.run("git branch -r", capture_output=True, text=True, shell=True)
        print("\nRemote deploy branches:")
        for line in result.stdout.split('\n'):
            if 'deploy-' in line:
                print(line.strip())
    
    elif command == 'setup':
        print("\n" + "="*50)
        print(" PHYS119 Configuration Setup")
        print("="*50)
        
        config = {}
        config['total_labs'] = 11  # Labs 0-10
        
        print("\nRepository URL (press Enter for default)")
        repo_input = input("Default [https://github.com/phys119/phys119]: ").strip()
        config['repo_url'] = repo_input if repo_input else "https://github.com/phys119/phys119"
        
        print("\nJupyterHub URL (press Enter for default)")
        hub_input = input("Default [https://phys119.phas.ubc.ca]: ").strip()
        config['hub_url'] = hub_input if hub_input else "https://phys119.phas.ubc.ca"
        
        print("\nCreate individual lab branches?")
        print("(in addition to cumulative branches)")
        individual = input("(y/n) [n]: ").lower().strip()
        config['create_individual_branches'] = individual == 'y'
        
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
        
        with open('phys119_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\n✓ Configuration saved to phys119_config.json")
        print("\nNext steps:")
        print("1. Run: python phys119_branch_manager.py update 0")
        print("   (This will create the branch for Lab 0)")
        print("2. Generate links: python generate_phys119_links.py")
        print("3. Add links to Canvas")
    
    else:
        print(f"Unknown command: {command}")
        print("Run 'python phys119_branch_manager.py' for usage information")
        sys.exit(1)

if __name__ == "__main__":
    main()
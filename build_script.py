# build_script.py
import os
import shutil
import subprocess
import sys
import time

def clean_previous_builds():
    """Remove previous build files and directories"""
    print("Cleaning previous builds...")
    
    items_to_remove = [
        'dist',
        'build', 
        '__pycache__',
        'LaboratoryEquipmentSystem.spec'
    ]
    
    for item in items_to_remove:
        try:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"Removed directory: {item}")
                else:
                    os.remove(item)
                    print(f"Removed file: {item}")
        except Exception as e:
            print(f"Could not remove {item}: {e}")

def delete_dist_and_build():
    """Specifically delete only dist and build directories"""
    print("Deleting dist and build folders...")
    
    directories_to_delete = [
        'dist',
        'build',
        r'C:\Users\allan\Desktop\capstone mysql version_mainserver\dist',
        r'C:\Users\allan\Desktop\capstone mysql version_mainserver\build'
    ]
    
    for directory in directories_to_delete:
        try:
            if os.path.exists(directory) and os.path.isdir(directory):
                shutil.rmtree(directory)
                print(f"Deleted: {directory}")
            else:
                print(f"Not found: {directory}")
        except Exception as e:
            print(f"Error deleting {directory}: {e}")

def check_required_files():
    """Check if required files exist before building"""
    print("Checking required files...")
    
    required_files = [
        'loginpage.py',
        'config.ini',
        'ion_logo.png',
        'background.jpg'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
            print(f"Missing: {file}")
        else:
            print(f"Found: {file}")
    
    if missing_files:
        print(f"Missing {len(missing_files)} required files. Build cancelled.")
        return False
    return True

def build_exe():
    """Build the EXE using PyInstaller"""
    print("Building EXE...")
    
    pyinstaller_cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=LaboratoryEquipmentSystem',
        '--hidden-import=pymysql',
        '--hidden-import=pymysql.cursors',
        '--hidden-import=pymysql.connections',
        '--hidden-import=PIL',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=configparser',
        '--add-data=ion_logo.png;.',
        '--add-data=background.jpg;.',
        '--add-data=config.ini;.',
        '--clean',
        'loginpage.py'
    ]
    
    pyinstaller_cmd = [arg for arg in pyinstaller_cmd if arg]
    
    try:
        print(f"Running: {' '.join(pyinstaller_cmd)}")
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True, check=True)
        
        if result.returncode == 0:
            print("Build completed successfully!")
            return True
        else:
            print(f"Build failed with return code: {result.returncode}")
            print(f"Error output: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller error: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("PyInstaller not found. Please install it with: pip install pyinstaller")
        return False

def verify_build():
    """Verify the EXE was built correctly"""
    print("Verifying build...")
    
    exe_path = 'dist/LaboratoryEquipmentSystem.exe'
    
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"EXE created: {exe_path}")
        print(f"File size: {file_size:.2f} MB")
        print(f"Location: {os.path.abspath(exe_path)}")
        print("Included files: ion_logo.png, background.jpg, config.ini")
        return True
    else:
        print("EXE not found in dist folder!")
        return False

def main():
    print("Starting Laboratory Equipment System Build Process")
    print("=" * 50)
    
    # Delete dist and build folders first
    delete_dist_and_build()
    print()
    
    # Step 1: Clean previous builds
    clean_previous_builds()
    print()
    
    # Step 2: Check required files
    if not check_required_files():
        return
    print()
    
    # Step 3: Build EXE
    start_time = time.time()
    if not build_exe():
        return
    build_time = time.time() - start_time
    print()
    
    # Step 4: Verify build
    if verify_build():
        print("=" * 50)
        print(f"Build completed in {build_time:.2f} seconds!")
        print("EXE is ready in the 'dist' folder")
    else:
        print("=" * 50)
        print("Build failed!")

if __name__ == "__main__":
    main()
"""
ThorLabs Camera Diagnostic Script
This script helps diagnose error 1004 and other ThorLabs SDK initialization issues.
"""

import os
import sys
import platform

def check_python_architecture():
    """Check if Python is 32-bit or 64-bit"""
    arch = platform.architecture()[0]
    print(f"Python Architecture: {arch}")
    if arch == "64bit":
        print("✓ Python is 64-bit (required for most ThorLabs SDKs)")
    else:
        print("✗ WARNING: Python is 32-bit. ThorLabs SDK typically requires 64-bit Python")
    return arch

def check_dll_directory():
    """Check if the DLL directory exists and contains required files"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dll_dir = os.path.join(script_dir, "cameras", "thor_drivers")
    
    print(f"\nDLL Directory: {dll_dir}")
    print(f"Exists: {os.path.exists(dll_dir)}")
    
    if os.path.exists(dll_dir):
        files = os.listdir(dll_dir)
        print(f"\nFound {len(files)} files in thor_drivers directory")
        
        # Check for critical DLLs
        critical_dlls = [
            "thorlabs_tsi_camera_sdk.dll",
            "thorlabs_tsi_mono_to_color_processing.dll"
        ]
        
        for dll in critical_dlls:
            if dll in files:
                print(f"✓ {dll} found")
            else:
                print(f"✗ {dll} NOT FOUND (required)")
    else:
        print("✗ DLL directory does not exist!")

def check_sdk_installation():
    """Check if ThorLabs SDK can be imported"""
    print("\n--- Checking SDK Import ---")
    try:
        import thorlabs_tsi_sdk
        print(f"✓ thorlabs_tsi_sdk module imported successfully")
        print(f"  Version/Path: {thorlabs_tsi_sdk.__file__}")
    except ImportError as e:
        print(f"✗ Failed to import thorlabs_tsi_sdk: {e}")
        return False
    return True

def check_running_processes():
    """Check for other processes that might be using the camera"""
    print("\n--- Checking for ThorCam Processes ---")
    try:
        import psutil
        thor_processes = []
        for proc in psutil.process_iter(['name']):
            try:
                if 'thor' in proc.info['name'].lower():
                    thor_processes.append(proc.info['name'])
            except:
                pass
        
        if thor_processes:
            print(f"⚠ Found ThorLabs processes: {thor_processes}")
            print("  These might be using the camera. Close them and try again.")
        else:
            print("✓ No ThorLabs processes detected")
    except ImportError:
        print("  (psutil not installed - skipping process check)")

def test_sdk_initialization():
    """Try to initialize the SDK"""
    print("\n--- Testing SDK Initialization ---")
    
    # Add DLL directory to path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dll_dir = os.path.join(script_dir, "cameras", "thor_drivers")
    
    if os.path.exists(dll_dir):
        os.add_dll_directory(dll_dir)
        os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')
        print(f"Added {dll_dir} to DLL search path")
    
    try:
        from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
        print("Attempting to open TLCameraSDK...")
        
        sdk = TLCameraSDK()
        print("✓ SDK initialized successfully!")
        
        # Discover cameras
        cameras = sdk.discover_available_cameras()
        print(f"✓ Found {len(cameras)} camera(s)")
        for i, serial in enumerate(cameras):
            print(f"  Camera {i}: {serial}")
        
        sdk.dispose()
        print("✓ SDK disposed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to initialize SDK: {e}")
        print(f"  Error type: {type(e).__name__}")
        
        if "1004" in str(e):
            print("\nError 1004 typically means:")
            print("  1. ThorCam software is not installed on this system")
            print("  2. SDK DLL files are missing or incompatible")
            print("  3. Required Visual C++ Redistributables are not installed")
            print("  4. Python architecture doesn't match DLL architecture")
            print("\nSuggested fixes:")
            print("  1. Install ThorCam software from Thorlabs website")
            print("  2. Install Visual C++ Redistributable 2015-2022 (x64)")
            print("  3. Ensure Python is 64-bit")
            print("  4. Copy DLLs from ThorCam installation directory")
        
        return False

def main():
    print("=" * 60)
    print("ThorLabs Camera Diagnostic Tool")
    print("=" * 60)
    
    check_python_architecture()
    check_dll_directory()
    check_sdk_installation()
    check_running_processes()
    test_sdk_initialization()
    
    print("\n" + "=" * 60)
    print("Diagnostic complete")
    print("=" * 60)

if __name__ == "__main__":
    main()


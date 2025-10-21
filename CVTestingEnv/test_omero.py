#!/usr/bin/env python3
"""
Quick test script to verify OMERO installation and configuration
"""
from omero_integration import OMEROManager
from dotenv import load_dotenv
import sys
import os


def test_omero_connection():
    """Test OMERO connection and basic operations"""
    print("=" * 60)
    print("OMERO Connection Test")
    print("=" * 60)
    
    manager = OMEROManager()

    # Check if configuration exists
    print("\n1. Checking configuration...")
    if not manager.host or not manager.username:
        print("⚠️  OMERO credentials not configured")
        print("   Set credentials in defualt.env or .env file")
        print("   See OMERO_SETUP.md for details")
        print("\n   Or test connection manually:")
        print("   manager.connect(host='server', username='user', password='pass')")
        return False

    print("✓ Configuration loaded")
    
    # Test connection
    print("\n2. Testing OMERO connection...")
    print(f"   Host: {manager.host}")
    print(f"   Port: {manager.port}")
    print(f"   Username: {manager.username}")
    
    if not manager.connect():
        print("\n✗ Connection failed!")
        print("\nTroubleshooting:")
        print("  1. Verify server is running")
        print("  2. Check hostname and port in .env")
        print("  3. Verify username and password")
        print("\nSee OMERO_SETUP.md for detailed troubleshooting")
        return False
    
    print("✓ Connected successfully!")
    
    # Test listing datasets
    print("\n3. Testing dataset access...")
    try:
        datasets = manager.list_datasets()
        print(f"✓ Found {len(datasets)} datasets")
        
        if datasets:
            print("\n   Available datasets:")
            for ds in datasets[:5]:  # Show first 5
                desc = ds['description'] if ds['description'] else 'No description'
                print(f"   - {ds['name']} (ID: {ds['id']})")
                print(f"     {desc}")
        else:
            print("   No datasets found (this is normal for a new server)")
            
    except Exception as e:
        print(f"⚠️  Error listing datasets: {e}")
    
    # Disconnect
    print("\n4. Disconnecting...")
    manager.disconnect()
    
    print("\n" + "=" * 60)
    print("✓ OMERO test completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  - Create a dataset for your images")
    print("  - Integrate with Image_Container for auto-upload")
    print("  - See OMERO_SETUP.md for more information")
    
    return True


def test_import_only():
    """Just test that OMERO modules can be imported"""
    print("=" * 60)
    print("OMERO Import Test")
    print("=" * 60)
    
    try:
        import omero
        print("✓ omero module imported")
        
        import omero.clients
        print("✓ omero.clients imported")
        
        import omero.gateway
        print("✓ omero.gateway imported")
        
        from omero.gateway import BlitzGateway
        print("✓ BlitzGateway imported")
        
        print("\n" + "=" * 60)
        print("✓ All OMERO modules imported successfully!")
        print("=" * 60)
        print("\nomero-py is properly installed and ready to use.")
        return True
        
    except ImportError as e:
        print(f"\n✗ Import failed: {e}")
        print("\nPlease reinstall omero-py:")
        print("  conda install -n automatedTransfer -c conda-forge omero-py --no-update-deps")
        return False


if __name__ == "__main__":
    print("\n")

    # Load default environment, then override with .env if it exists
    load_dotenv("defualt.env")
    load_dotenv(".env", override=True)

    # First test imports
    if not test_import_only():
        sys.exit(1)
    
    print("\n")
    
    # Then test connection if configured
    if any(os.getenv(key) for key in ['OMERO_HOST', 'OMERO_USERNAME']):
        test_omero_connection()
    else:
        print("=" * 60)
        print("Skipping connection test (no .env file)")
        print("=" * 60)
        print("\nTo test connection:")
        print("  1. Create .env file with OMERO credentials")
        print("  2. Run this script again")
        print("\nSee OMERO_SETUP.md for configuration details")


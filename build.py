#!/usr/bin/env python3
"""
FORGE Build Script
Orchestrates the complete build process for Windows distribution
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
LAUNCHER_DIR = PROJECT_ROOT / "launcher"

def run_command(cmd, cwd=None, shell=False):
    """Run a command and check for errors"""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=cwd, shell=shell, check=False)
    if result.returncode != 0:
        print(f"ERROR: Command failed with code {result.returncode}")
        sys.exit(1)
    print("✓ Command completed successfully")
    return result

def clean():
    """Clean previous build artifacts"""
    print("\n🧹 Cleaning previous builds...")
    for dir_path in [BUILD_DIR, DIST_DIR, LAUNCHER_DIR / "dist"]:
        if dir_path.exists():
            print(f"  Removing {dir_path}")
            shutil.rmtree(dir_path)
    print("✓ Clean complete")

def build_backend():
    """Freeze backend with PyInstaller"""
    print("\n🔨 Building backend executable...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Run PyInstaller
    spec_file = PROJECT_ROOT / "backend" / "forge_backend.spec"
    run_command([
        sys.executable, "-m", "PyInstaller",
        str(spec_file),
        "--distpath", str(DIST_DIR / "backend"),
        "--workpath", str(BUILD_DIR / "backend"),
        "--noconfirm"
    ])
    
    print("✓ Backend build complete")

def build_frontend():
    """Build frontend static assets"""
    print("\n🎨 Building frontend...")
    
    frontend_dir = PROJECT_ROOT / "frontend"
    
    # Install dependencies
    print("  Installing frontend dependencies...")
    run_command(["npm", "install"], cwd=frontend_dir, shell=True)
    
    # Build production assets
    print("  Building production assets...")
    run_command(["npm", "run", "build"], cwd=frontend_dir, shell=True)
    
    # Copy build output to dist
    frontend_dist = frontend_dir / "dist"
    if frontend_dist.exists():
        shutil.copytree(frontend_dist, DIST_DIR / "frontend", dirs_exist_ok=True)
        print("✓ Frontend build complete")
    else:
        print("ERROR: Frontend build directory not found")
        sys.exit(1)

def package_electron():
    """Package Electron application with NSIS installer"""
    print("\n📦 Packaging Electron application...")
    
    # Verify that backend and frontend builds exist
    backend_exe = DIST_DIR / "backend" / "forge-backend.exe"
    if not backend_exe.exists():
        print(f"ERROR: Backend executable not found at {backend_exe}")
        print("Run with --backend first to build the backend")
        sys.exit(1)
    
    if not (DIST_DIR / "frontend").exists():
        print(f"ERROR: Frontend build not found at {DIST_DIR / 'frontend'}")
        print("Run with --frontend first to build the frontend")
        sys.exit(1)
    
    print(f"  Backend found: {backend_exe}")
    print(f"  Frontend found: {DIST_DIR / 'frontend'}")
    
    # Install launcher dependencies
    print("  Installing launcher dependencies...")
    run_command(["npm", "install"], cwd=LAUNCHER_DIR, shell=True)
    
    # Build with electron-builder (creates NSIS installer)
    # electron-builder will automatically package extraResources from ../dist/
    print("  Building Electron package with NSIS installer...")
    run_command(["npm", "run", "dist"], cwd=LAUNCHER_DIR, shell=True)
    
    print("✓ Electron packaging complete")
    print("  Installer will be in: launcher/dist/")
    print("  Look for FORGE Setup X.X.X.exe")

def main():
    """Main build process"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                     FORGE BUILD TOOL                      ║
║              Where Concepts Become Systems                ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    if "--clean" in sys.argv:
        clean()
        if "--clean-only" in sys.argv:
            return
    
    try:
        # Build backend
        if "--backend" in sys.argv or "--all" in sys.argv:
            build_backend()
        
        # Build frontend
        if "--frontend" in sys.argv or "--all" in sys.argv:
            build_frontend()
        
        # Package Electron (includes NSIS installer)
        if "--electron" in sys.argv or "--all" in sys.argv:
            package_electron()
        
        if not any(arg in sys.argv for arg in ["--backend", "--frontend", "--electron", "--all"]):
            print("\nUsage: python build.py [options]")
            print("\nOptions:")
            print("  --all         Build everything (backend + frontend + Electron NSIS installer)")
            print("  --backend     Build backend only")
            print("  --frontend    Build frontend only")
            print("  --electron    Package Electron app with installer")
            print("  --clean       Clean before building")
            print("  --clean-only  Clean and exit")
            print("\nExample: python build.py --all --clean")
            print("\nNOTE: The --electron step creates both the app and Windows NSIS installer.")
            return
        
        print(f"\n{'='*60}")
        print("✨ BUILD COMPLETE!")
        print(f"{'='*60}")
        print(f"\nDistribution files are in: {DIST_DIR}")
        print(f"Launcher package is in: {LAUNCHER_DIR / 'dist'}")
        
    except KeyboardInterrupt:
        print("\n\n❌ Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

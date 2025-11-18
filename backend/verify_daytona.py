#!/usr/bin/env python3
import sys
import time
import os

# Add current directory to path to import app
sys.path.append(".")

def verify_daytona():
    print("=" * 60)
    print("Daytona Setup Verification")
    print("=" * 60)

    # 1. Check Imports
    try:
        import daytona
        from daytona import Daytona, CreateSandboxFromSnapshotParams
        print("  [OK] daytona SDK imported")
    except ImportError as e:
        print(f"  [FAIL] Could not import daytona: {e}")
        print(f"  sys.path: {sys.path}")
        return

    try:
        from app.core.config import settings
        print("  [OK] App settings loaded")
    except ImportError:
        print("  [FAIL] Could not import app.core.config. Run this from backend directory.")
        return

    # 2. Check Configuration
    print(f"\n[*] Checking Configuration:")
    print(f"  DAYTONA_ENABLED: {settings.DAYTONA_ENABLED}")
    print(f"  Default Language: {settings.DAYTONA_DEFAULT_LANGUAGE}")
    
    api_key = settings.DAYTONA_API_KEY
    if api_key:
        masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
        print(f"  DAYTONA_API_KEY: {masked_key}")
    else:
        print("  DAYTONA_API_KEY: [NOT SET]")

    if not settings.DAYTONA_ENABLED:
        print("\n[SKIP] Daytona is disabled in settings. Set DAYTONA_ENABLED=true in .env to test.")
        return

    # 3. Test SDK
    print("\n[*] Testing Daytona SDK:")
    try:
        from daytona import DaytonaConfig
        config = DaytonaConfig(
            api_key=settings.DAYTONA_API_KEY or None,
            api_url=settings.DAYTONA_API_URL,
            target=settings.DAYTONA_TARGET
        )
        daytona = Daytona(config=config)
        print("  [OK] Daytona SDK initialized")
        
        print("  Creating sandbox (this may take a moment)...")
        start_time = time.time()
        params = CreateSandboxFromSnapshotParams(language=settings.DAYTONA_DEFAULT_LANGUAGE)
        sandbox = daytona.create(params)
        duration = time.time() - start_time
        print(f"  [OK] Sandbox created in {duration:.2f}s")
        
        print("  Running 'echo Hello Daytona'...")
        response = sandbox.process.exec('echo "Hello Daytona"')
        if response.result:
             print(f"  [Output] {response.result.strip()}")
        
        if response.result and "Hello Daytona" in response.result:
            print("  [OK] Execution verified")
        else:
            print(f"  [FAIL] Unexpected output: {response.result}")
            
        print("  Removing sandbox...")
        daytona.delete(sandbox)
        print("  [OK] Sandbox removed")
        
        print("\n[SUCCESS] Daytona integration is working!")
        
    except Exception as e:
        print(f"\n[FAIL] Daytona test failed: {e}")
        print("Troubleshooting:")
        print("1. Ensure Daytona server is running (if local)")
        print("2. Check your Daytona API keys/auth if required")
        print("3. Verify internet connection")
        # Print full traceback for debugging
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_daytona()


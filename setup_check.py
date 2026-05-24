#!/usr/bin/env python3
"""
Quick Setup Script for Enhanced CSS/PMS Portal
Verifies all dependencies and configurations before starting
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """Verify Python version."""
    print("✓ Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  Python {version.major}.{version.minor}.{version.micro} ✓")
        return True
    else:
        print(f"  ✗ Python 3.8+ required (found {version.major}.{version.minor})")
        return False

def check_required_packages():
    """Check for required Python packages."""
    print("\n✓ Checking required packages...")
    required = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'chromadb': 'ChromaDB',
        'sentence_transformers': 'SentenceTransformers',
        'rank_bm25': 'BM25',
        'openai': 'OpenAI',
        'sqlalchemy': 'SQLAlchemy'
    }
    
    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED")
            missing.append(module)
    
    if missing:
        print(f"\nInstalling missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
        print("  ✓ Installation complete")
    
    return True

def check_openai_api_key():
    """Check if OpenAI API key is configured."""
    print("\n✓ Checking OpenAI API Key...")
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("  ✗ OPENAI_API_KEY not set")
        print("\nTo set it:")
        print("  Windows (PowerShell): $env:OPENAI_API_KEY = 'your-key'")
        print("  Windows (CMD): set OPENAI_API_KEY=your-key")
        print("  Linux/Mac: export OPENAI_API_KEY='your-key'")
        return False
    
    if len(api_key) < 20:
        print("  ✗ API key appears invalid (too short)")
        return False
    
    print("  ✓ API key configured")
    return True

def check_database():
    """Check if database directory exists."""
    print("\n✓ Checking database directory...")
    db_path = r"e:\css\chroma_db"
    if os.path.exists(db_path):
        print(f"  ✓ Database path: {db_path}")
        return True
    else:
        print(f"  ✗ Database path not found: {db_path}")
        print("    Creating directory...")
        os.makedirs(db_path, exist_ok=True)
        print("  ✓ Created")
        return True

def check_data_files():
    """Check if source data files exist."""
    print("\n✓ Checking data files...")
    base_dir = r"e:\css"
    files_to_check = [
        ("css_notes_rag.jsonl", "CSS notes"),
        ("pms_notes_rag.jsonl", "PMS notes"),
    ]
    dirs_to_check = [
        (r"CSS_Banks\english essay", "Essay files"),
    ]
    
    all_exist = True
    for file_name, description in files_to_check:
        file_path = os.path.join(base_dir, file_name)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / 1024  # KB
            print(f"  ✓ {description}: {file_name} ({size:.1f} KB)")
        else:
            print(f"  ✗ {description}: {file_name} - NOT FOUND")
            all_exist = False
    
    for dir_name, description in dirs_to_check:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.isdir(dir_path):
            file_count = len(list(Path(dir_path).glob("*.txt")))
            print(f"  ✓ {description}: {dir_name} ({file_count} files)")
        else:
            print(f"  ✗ {description}: {dir_name} - NOT FOUND")
            all_exist = False
    
    return all_exist

def show_next_steps():
    """Display next steps."""
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("\n1. RUN ENHANCED DATA INGESTION:")
    print("   cd backend")
    print("   python ingest_enhanced.py")
    print("\n2. START FLASK SERVER:")
    print("   python main.py")
    print("\n3. TEST THE SYSTEM:")
    print("   curl -X POST http://localhost:5000/api/chat \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"query\": \"What is PMS\"}'")
    print("\n4. VERIFY PMS DEFINITION IS CORRECT:")
    print("   Response should mention: 'Provincial Management Service'")
    print("\n" + "="*70)

def main():
    """Run all checks."""
    print("="*70)
    print("CSS/PMS PORTAL - ENHANCED SETUP CHECK")
    print("="*70)
    
    checks = [
        ("Python Version", check_python),
        ("Required Packages", check_required_packages),
        ("OpenAI API Key", check_openai_api_key),
        ("Database Directory", check_database),
        ("Data Files", check_data_files),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results[check_name] = False
    
    print("\n" + "="*70)
    print("SETUP CHECK SUMMARY")
    print("="*70)
    
    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ All checks passed! System is ready.")
        show_next_steps()
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        if not results["OpenAI API Key"]:
            print("\nIMPORTANT: Set your OpenAI API key before proceeding!")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

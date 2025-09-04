#!/usr/bin/env python3
"""
Final verification script to confirm all emojis have been removed from the codebase
"""

import os
import re
from pathlib import Path

def find_emojis_in_file(filepath):
    """Find emojis in a specific file"""
    emojis_found = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Emoji Unicode ranges
        emoji_patterns = [
            r'[\u{1F600}-\u{1F64F}]',  # Emoticons
            r'[\u{1F300}-\u{1F5FF}]',  # Misc Symbols and Pictographs
            r'[\u{1F680}-\u{1F6FF}]',  # Transport and Map
            r'[\u{1F1E0}-\u{1F1FF}]',  # Regional indicator symbols
            r'[\u{2600}-\u{26FF}]',    # Misc symbols
            r'[\u{2700}-\u{27BF}]',    # Dingbats
            r'[\u{1f926}-\u{1f937}]',  # Gestures
            r'[\u{1f1f2}-\u{1f1f4}]',  # Regional indicators
            r'[\u{1f191}-\u{1f19a}]',  # Squared symbols
        ]

        for pattern in emoji_patterns:
            matches = re.findall(pattern, content)
            if matches:
                emojis_found.extend(matches)

    except Exception as e:
        print(f"[ERROR] Could not read {filepath}: {e}")

    return emojis_found

def scan_codebase_for_emojis():
    """Scan the entire codebase for any remaining emojis"""
    print("[SCAN] Scanning codebase for emojis...")

    emoji_files = []
    total_emojis = 0

    for root, dirs, files in os.walk('.'):
        # Skip common directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]

        for file in files:
            if file.endswith(('.py', '.md', '.html', '.txt', '.json', '.yml', '.yaml')):
                filepath = os.path.join(root, file)
                emojis = find_emojis_in_file(filepath)
                if emojis:
                    emoji_files.append((filepath, emojis))
                    total_emojis += len(emojis)
                    print(f"    [FOUND] {filepath}: {len(emojis)} emojis")
                    for emoji in emojis:
                        print(f"        {emoji}")

    return emoji_files, total_emojis

def main():
    """Main verification function"""
    print("=" * 60)
    print("OpenWorld Specialty Chemicals - Emoji Verification")
    print("=" * 60)

    emoji_files, total_emojis = scan_codebase_for_emojis()

    print(f"\n[RESULTS] Scan complete")
    print(f"Files with emojis: {len(emoji_files)}")
    print(f"Total emojis found: {total_emojis}")

    if total_emojis == 0:
        print("\n[SUCCESS] [SUCCESS] All emojis have been successfully removed from the codebase!")
        print("[CLEAN] The codebase is now emoji-free and professional.")
        print("\nProfessional text replacements used:")
        print("  [ERROR] emoji → [ERROR]")
        print("  [SUCCESS] emoji → [SUCCESS]")
        print("  [WARNING] emoji → [WARNING]")
        print("  [DATA] emoji → [DATA]")
        print("  [ADVICE] emoji → [ADVICE]")
        print("  [REPORT] emoji → [REPORT]")
        print("  [STREAM] emoji → [STREAM]")
        print("  [START] emoji → [START]")
        print("  [INFO] emoji → [INFO]")
        print("  And many more...")
        return True
    else:
        print(f"\n[WARNING] [ERROR] Found {total_emojis} emojis in {len(emoji_files)} files")
        print("Files that still contain emojis:")
        for filepath, emojis in emoji_files:
            print(f"  - {filepath}: {len(emojis)} emojis")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

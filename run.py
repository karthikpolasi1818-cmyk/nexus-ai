from __future__ import annotations

import os
import subprocess
import sys


PROJECT_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

APP_FILE = os.path.join(
    PROJECT_ROOT,
    "app",
    "main.py"
)


def main():

    print()
    print("=" * 70)
    print("                 🧠 NEXUS AI")
    print("        Autonomous Enterprise Intelligence")
    print("=" * 70)

    print()
    print(f"📁 Project : {PROJECT_ROOT}")
    print(f"🚀 App     : {APP_FILE}")

    if not os.path.exists(APP_FILE):

        print()
        print("❌ ERROR: app/main.py was not found.")
        print()
        sys.exit(1)

    print()
    print("✅ Project structure detected.")
    print("🚀 Starting NEXUS AI...")
    print()
    print("🌐 URL:")
    print("   http://localhost:8501")
    print()
    print("💡 Press Ctrl+C to stop NEXUS AI.")
    print()
    print("-" * 70)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            APP_FILE,
            "--server.port",
            "8501"
        ],
        cwd=PROJECT_ROOT
    )


if __name__ == "__main__":
    main()
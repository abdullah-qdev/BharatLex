#!/usr/bin/env python3
"""
Quick setup script to help run the React dev server and backend in parallel.
"""
import subprocess
import time
import sys
import os

def run_command(cmd, name, cwd=None):
    """Run a command in a subprocess."""
    print(f"🚀 Starting {name}...")
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd or os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        return process
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

if __name__ == "__main__":
    print("🎤 BharatLex Development Server Setup\n")
    
    # Backend is already running (uvicorn)
    print("✅ Backend should be running on http://127.0.0.1:8000")
    print("📝 Create a `.env` file in the project root with:")
    print("   GROQ_API_KEY=your_key_here")
    print("   SARVAM_API_KEY=your_key_here\n")
    
    print("For now, use these endpoints:")
    print("  - Demo: http://127.0.0.1:8000/demo-analyze")
    print("  - Upload: POST http://127.0.0.1:8000/analyze-audio")
    print("  - Health: http://127.0.0.1:8000/ping\n")
    
    print("To test the full flow:")
    print("  1. Open mic_test.html in your browser")
    print("  2. Click 🎬 Demo Mode to see it work")
    print("  3. Record audio and click Stop & Analyze\n")
    
    print("If you want a React app, run:")
    print("  npm create vite@latest bharatlex-web -- --template react")
    print("  cd bharatlex-web && npm install && npm run dev")

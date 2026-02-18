from dotenv import load_dotenv
load_dotenv()

import uvicorn
import os

if __name__ == "__main__":
    print("\n" + "="*70)
    print("EMAIL AGENT - HITL WEB SERVER")
    print("="*70)
    print(f"\n🌐 Starting server on: http://localhost:8000")
    print(f"📊 Dashboard URL:      http://localhost:8000")
    print(f"🔌 WebSocket URL:      ws://localhost:8000/ws")
    print(f"❤️  Health Check:       http://localhost:8000/health")
    print(f"\nPress Ctrl+C to stop\n")
    print("="*70 + "\n")
    
    uvicorn.run(
        "ui.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="warning"  # Reduce noise
    )
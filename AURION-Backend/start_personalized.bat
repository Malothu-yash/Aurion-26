@echo off
cls
color 0B
echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                                                                        ║
echo ║     █████╗ ██╗   ██╗██████╗ ██╗ ██████╗ ███╗   ██╗                   ║
echo ║    ██╔══██╗██║   ██║██╔══██╗██║██╔═══██╗████╗  ██║                   ║
echo ║    ███████║██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║                   ║
echo ║    ██╔══██║██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║                   ║
echo ║    ██║  ██║╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║                   ║
echo ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝                   ║
echo ║                                                                        ║
echo ║              Your Intelligent Personalized AI Assistant               ║
echo ║                        Version 2.0 - Full Personalization             ║
echo ║                                                                        ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.
echo ┌────────────────────────────────────────────────────────────────────────┐
echo │  ✨ NEW FEATURES ENABLED                                               │
echo ├────────────────────────────────────────────────────────────────────────┤
echo │  ✓ Answers ALL questions (general knowledge + personal)                │
echo │  ✓ Deep personalization (remembers everything about you)               │
echo │  ✓ Enhanced memory (Redis + Pinecone + Neo4j + Profile)                │
echo │  ✓ Continuous learning (learns from every interaction)                 │
echo │  ✓ Smart context awareness (tracks topics, interests, style)           │
echo │  ✓ Communication style adaptation (casual, professional, detailed)     │
echo │  ✓ Personalized recommendations (based on your interests)              │
echo └────────────────────────────────────────────────────────────────────────┘
echo.
echo [1/3] Stopping any running backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul >nul
timeout /t 1 /nobreak >nul

echo [2/3] Initializing AURION with full personalization...
echo.
echo ┌────────────────────────────────────────────────────────────────────────┐
echo │  📍 Backend URL:  http://127.0.0.1:8000                                │
echo │  📍 Frontend URL: http://localhost:3000                                │
echo │  📍 Status:       Starting...                                          │
echo └────────────────────────────────────────────────────────────────────────┘
echo.
echo [3/3] Launching backend server...
echo.
echo 💡 TIP: Try these commands:
echo    - "My name is [Name] and I love [Interest]"
echo    - "What's my name?"
echo    - "Recommend something for me"
echo    - "What is pi?"
echo.
echo Press Ctrl+C to stop the server
echo.
echo ════════════════════════════════════════════════════════════════════════
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

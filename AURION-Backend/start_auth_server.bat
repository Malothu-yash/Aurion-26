@echo off
echo Starting AURION Backend with Authentication...
cd /d c:\Users\vamsh\Source\3_1\project_ps2\AURION\AURION-Backend
python -m uvicorn app.main:app --reload --port 8000

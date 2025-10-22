import sys
sys.path.insert(0, '.')

with open('app/main.py', 'a') as f:
    f.write('\n\n# --- Mount Socket.IO for Admin Real-Time ---\n')
    f.write('from app.admin.realtime import socket_app\n')
    f.write('app.mount("/socket.io", socket_app)\n')

print("Socket.IO mount added to main.py")

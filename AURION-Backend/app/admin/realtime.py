# app/admin/realtime.py
# Real-time Socket.IO integration for admin dashboard

import socketio
from typing import Dict, Set
import asyncio
from app.core.config import settings

# Parse allowed origins from settings
allowed_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=allowed_origins,  # Use environment variable instead of '*'
    logger=True,
    engineio_logger=True
)

# Store connected admin clients
admin_clients: Set[str] = set()

# ===========================
# Socket.IO Event Handlers
# ===========================

@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    print(f"Admin client connected: {sid}")
    admin_clients.add(sid)
    
    # Send initial connection confirmation
    await sio.emit('connected', {'sid': sid}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Admin client disconnected: {sid}")
    admin_clients.discard(sid)

@sio.event
async def authenticate(sid, data):
    """Authenticate admin connection with JWT token"""
    try:
        from app.admin.auth import verify_token
        token = data.get('token')
        
        if not token:
            await sio.emit('auth_error', {'error': 'No token provided'}, room=sid)
            return
        
        payload = verify_token(token)
        
        if payload:
            # Store admin info with session
            await sio.save_session(sid, {'admin': payload})
            await sio.emit('authenticated', {'success': True}, room=sid)
        else:
            await sio.emit('auth_error', {'error': 'Invalid token'}, room=sid)
    except Exception as e:
        await sio.emit('auth_error', {'error': str(e)}, room=sid)

@sio.event
async def subscribe_stats(sid, data):
    """Subscribe to real-time stats updates"""
    print(f"Client {sid} subscribed to stats")
    await sio.enter_room(sid, 'stats')
    
    # Send initial stats
    from app.admin.services import admin_services
    stats = await admin_services.get_system_stats()
    api_stats = await admin_services.get_api_usage_stats()
    
    await sio.emit('stats_update', {
        'system': stats,
        'api_usage': api_stats
    }, room=sid)

@sio.event
async def subscribe_logs(sid, data):
    """Subscribe to real-time log updates"""
    print(f"Client {sid} subscribed to logs")
    await sio.enter_room(sid, 'logs')

@sio.event
async def unsubscribe_stats(sid, data):
    """Unsubscribe from stats updates"""
    await sio.leave_room(sid, 'stats')

@sio.event
async def unsubscribe_logs(sid, data):
    """Unsubscribe from log updates"""
    await sio.leave_room(sid, 'logs')

# ===========================
# Broadcast Functions
# ===========================

async def broadcast_stats():
    """Broadcast system stats to all connected admins"""
    from app.admin.services import admin_services
    
    while True:
        try:
            if admin_clients:
                stats = await admin_services.get_system_stats()
                api_stats = await admin_services.get_api_usage_stats()
                
                await sio.emit('stats_update', {
                    'system': stats,
                    'api_usage': api_stats
                }, room='stats')
        except Exception as e:
            print(f"Error broadcasting stats: {e}")
        
        await asyncio.sleep(5)  # Update every 5 seconds

async def broadcast_log(log_type: str, log_data: Dict):
    """Broadcast log message to subscribed admins"""
    try:
        await sio.emit('log_update', {
            'type': log_type,
            'data': log_data
        }, room='logs')
    except Exception as e:
        print(f"Error broadcasting log: {e}")

async def broadcast_alert(alert_type: str, message: str, details: Dict = None):
    """Broadcast alert to all admin clients"""
    try:
        await sio.emit('alert', {
            'type': alert_type,  # info, warning, error, success
            'message': message,
            'details': details or {}
        })
    except Exception as e:
        print(f"Error broadcasting alert: {e}")

async def broadcast_user_action(action: str, user_id: str, details: Dict = None):
    """Broadcast user action to all admins"""
    try:
        await sio.emit('user_action', {
            'action': action,
            'user_id': user_id,
            'details': details or {}
        })
    except Exception as e:
        print(f"Error broadcasting user action: {e}")

# ===========================
# Background Tasks
# ===========================

async def start_background_tasks():
    """Start background tasks for real-time updates"""
    asyncio.create_task(broadcast_stats())

# Create ASGI app for Socket.IO
socket_app = socketio.ASGIApp(sio, socketio_path='socket.io')

#!/usr/bin/env python3
"""
Quick script to view all users in MongoDB database
Run: python view_my_data.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# MongoDB connection
from app.core.config import settings
MONGO_URI = getattr(settings, 'mongo_uri', None)
DATABASE = getattr(settings, 'mongo_db_name', 'aurion')

async def view_all_users():
    """View all registered users in the database"""
    
    print("\n" + "="*60)
    print("🔍 VIEWING YOUR SIGNUP DATA FROM MONGODB")
    print("="*60 + "\n")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE]
    
    try:
        # Count total users
        total = await db.users.count_documents({})
        print(f"📊 Total Users in Database: {total}\n")
        
        if total == 0:
            print("❌ No users found. Sign up first at http://localhost:5173\n")
            return
        
        # Get all users
        users = await db.users.find().to_list(100)
        
        print("👥 USER LIST:")
        print("-" * 60)
        
        for i, user in enumerate(users, 1):
            print(f"\n{i}. USER DETAILS:")
            print(f"   📧 Email: {user.get('email', 'N/A')}")
            print(f"   👤 Name: {user.get('display_name', 'N/A')}")
            print(f"   💼 Role: {user.get('role', 'N/A')}")
            print(f"   ❤️  Hobbies: {', '.join(user.get('hobbies', []))}")
            print(f"   📅 Created: {user.get('created_at', 'N/A')}")
            print(f"   ✅ Verified: {user.get('verified', False)}")
            print(f"   🔐 Password: [HASHED - {user.get('password', '')[:30]}...]")
            print(f"   🆔 MongoDB ID: {user.get('_id', 'N/A')}")
        
        print("\n" + "-" * 60)
        print("\n✅ Data retrieved successfully from MongoDB Atlas!")
        print("🌐 Database: Aurion")
        print("📁 Collection: users")
        print("🔗 Dashboard: https://cloud.mongodb.com/\n")
        
    except Exception as e:
        print(f"\n❌ Error connecting to MongoDB: {e}")
        print("Make sure your backend server is running!\n")
    
    finally:
        client.close()

async def view_otps():
    """View active OTPs (temporary data)"""
    
    print("\n" + "="*60)
    print("🔑 VIEWING ACTIVE OTPs")
    print("="*60 + "\n")
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE]
    
    try:
        # Count active OTPs
        total = await db.otps.count_documents({})
        print(f"📊 Active OTPs: {total}\n")
        
        if total == 0:
            print("✅ No active OTPs (all expired or used)\n")
            return
        
        # Get all OTPs
        otps = await db.otps.find().to_list(100)
        
        for i, otp in enumerate(otps, 1):
            print(f"{i}. Email: {otp.get('email', 'N/A')}")
            print(f"   OTP: {otp.get('otp', 'N/A')}")
            print(f"   Purpose: {otp.get('purpose', 'N/A')}")
            print(f"   Created: {otp.get('created_at', 'N/A')}")
            print(f"   Expires: {otp.get('expires_at', 'N/A')}")
            print(f"   Attempts: {otp.get('attempts', 0)}/{otp.get('max_attempts', 3)}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    finally:
        client.close()

async def main():
    """Main function"""
    
    print("\n🚀 AURION DATA VIEWER")
    print("=" * 60)
    
    # View users
    await view_all_users()
    
    # View OTPs (optional)
    print("\n" + "="*60)
    choice = input("Want to see active OTPs? (y/n): ").strip().lower()
    if choice == 'y':
        await view_otps()
    
    print("\n" + "="*60)
    print("✨ Done! Your data is safely stored in MongoDB Atlas.")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Exited by user\n")

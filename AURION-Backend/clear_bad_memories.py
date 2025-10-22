"""
Clear error messages from Redis chat history
This will remove all the "I'm sorry, I'm having trouble processing" responses
"""

import asyncio
import redis.asyncio as redis
import json
from dotenv import load_dotenv
import os

load_dotenv()

async def clear_bad_memories():
    """Remove error messages from chat history"""
    print("\n" + "="*60)
    print("🧹 Cleaning Bad Memories from Redis")
    print("="*60)
    
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("❌ REDIS_URL not found in .env")
        return
    
    try:
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Get all keys
        all_keys = await client.keys("chat:*")
        print(f"\n📊 Found {len(all_keys)} chat history keys")
        
        error_phrases = [
            "i'm sorry, i'm having trouble processing",
            "i'm having trouble",
            "processing that request",
            "critical error occurred",
            "an error occurred",
            "thought process:",
            "analyze the user query"
        ]
        
        total_removed = 0
        
        for key in all_keys:
            # Get all messages in this chat
            messages = await client.lrange(key, 0, -1)
            
            cleaned_messages = []
            removed_count = 0
            
            for msg_str in messages:
                try:
                    msg = json.loads(msg_str)
                    msg_content = str(msg.get('content', '')).lower()
                    
                    # Check if this message contains error phrases
                    is_error = any(phrase in msg_content for phrase in error_phrases)
                    
                    if not is_error:
                        cleaned_messages.append(msg_str)
                    else:
                        removed_count += 1
                        print(f"  🗑️  Removing: {msg_content[:80]}...")
                
                except json.JSONDecodeError:
                    # Keep non-JSON messages
                    cleaned_messages.append(msg_str)
            
            if removed_count > 0:
                # Delete the old key
                await client.delete(key)
                
                # Re-add cleaned messages
                if cleaned_messages:
                    await client.rpush(key, *cleaned_messages)
                    # Restore TTL (24 hours)
                    await client.expire(key, 86400)
                
                print(f"✅ {key}: Removed {removed_count} error messages")
                total_removed += removed_count
        
        await client.aclose()
        
        print("\n" + "="*60)
        print(f"🎉 Cleanup Complete!")
        print(f"📊 Total error messages removed: {total_removed}")
        print("="*60)
        
        if total_removed > 0:
            print("\n✅ Your chat history is now clean!")
            print("💬 Try sending 'Hello' again - it should work now")
        else:
            print("\n✅ No error messages found - chat history is already clean")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clear_bad_memories())

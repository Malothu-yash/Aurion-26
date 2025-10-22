# app/admin/services.py
# Admin services for user management, system stats, etc.

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import app.auth_db as auth_db_module
from app.services.memory import redis_pool, neo4j_driver
import psutil
import os

class AdminServices:
    """Admin services for dashboard operations"""
    
    @staticmethod
    async def get_system_stats() -> Dict:
        """Get overall system statistics"""
        try:
            # User statistics
            total_users = await auth_db_module.db.users.count_documents({})
            active_users = await auth_db_module.db.users.count_documents({
                "last_login": {"$gte": datetime.utcnow() - timedelta(days=7)}
            })
            suspended_users = await auth_db_module.db.users.count_documents({"status": "suspended"})
            inactive_users = total_users - active_users - suspended_users
            
            # Server statistics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            # Calculate uptime (you might want to store server start time)
            uptime = 0  # Will be calculated from server start time
            
            # Memory usage from Neo4j (approximate)
            total_memory_mb = 0
            try:
                if neo4j_driver:
                    # Query to get memory node count
                    async with neo4j_driver.session() as session:
                        result = await session.run("MATCH (n) RETURN count(n) as count")
                        record = await result.single()
                        if record:
                            node_count = record["count"]
                            # Rough estimate: 1KB per node
                            total_memory_mb = node_count / 1024
            except Exception as e:
                print(f"Error getting Neo4j stats: {e}")
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "suspended_users": suspended_users,
                "total_memory_usage": round(total_memory_mb, 2),
                "server_uptime": uptime,
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "inactive_users": 0,
                "suspended_users": 0,
                "total_memory_usage": 0,
                "server_uptime": 0,
                "cpu_usage": 0,
                "memory_usage": 0,
                "timestamp": datetime.utcnow()
            }
    
    @staticmethod
    async def get_all_users(
        skip: int = 0, 
        limit: int = 50, 
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict:
        """Get all users with pagination and filters"""
        query = {}
        
        if search:
            query["$or"] = [
                {"email": {"$regex": search, "$options": "i"}},
                {"display_name": {"$regex": search, "$options": "i"}}
            ]
        
        if status:
            if status == "active":
                query["last_login"] = {"$gte": datetime.utcnow() - timedelta(days=7)}
            elif status == "suspended":
                query["status"] = "suspended"
            elif status == "inactive":
                query["last_login"] = {"$lt": datetime.utcnow() - timedelta(days=7)}
        
        total = await auth_db_module.db.users.count_documents(query)
        users = await auth_db_module.db.users.find(query).skip(skip).limit(limit).to_list(length=limit)
        
        # Convert ObjectId to string
        for user in users:
            user["_id"] = str(user["_id"])
            user["password"] = "***"  # Don't send passwords
        
        return {
            "total": total,
            "users": users,
            "page": skip // limit + 1,
            "pages": (total + limit - 1) // limit
        }
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Get user details by ID"""
        from bson.objectid import ObjectId
        try:
            user = await auth_db_module.db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
                user["password"] = "***"
            return user
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    @staticmethod
    async def update_user(user_id: str, updates: Dict) -> bool:
        """Update user details"""
        from bson.objectid import ObjectId
        try:
            result = await auth_db_module.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    @staticmethod
    async def delete_user(user_id: str) -> bool:
        """Delete user"""
        from bson.objectid import ObjectId
        try:
            result = await auth_db_module.db.users.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    @staticmethod
    async def get_user_memory_stats(user_id: str) -> Dict:
        """Get user's memory usage statistics"""
        try:
            # Query Neo4j for user's memory nodes
            if not neo4j_driver:
                return {"total_memories": 0, "memory_size_kb": 0}
            
            async with neo4j_driver.session() as session:
                result = await session.run(
                    """
                    MATCH (n {userId: $user_id})
                    RETURN count(n) as count
                    """,
                    user_id=user_id
                )
                record = await result.single()
                count = record["count"] if record else 0
                
                # Rough estimate of memory size
                memory_size_kb = count * 1  # 1KB per memory node
                
                return {
                    "total_memories": count,
                    "memory_size_kb": memory_size_kb,
                    "memory_size_mb": round(memory_size_kb / 1024, 2)
                }
        except Exception as e:
            print(f"Error getting memory stats: {e}")
            return {"total_memories": 0, "memory_size_kb": 0}
    
    @staticmethod
    async def get_api_usage_stats() -> List[Dict]:
        """Get API usage statistics from Redis"""
        try:
            stats = []
            providers = ["groq", "gemini", "openai", "mistral", "claude"]
            
            for provider in providers:
                # Get stats from Redis (you'll need to implement tracking)
                total_key = f"api:stats:{provider}:total"
                success_key = f"api:stats:{provider}:success"
                failed_key = f"api:stats:{provider}:failed"
                
                if redis_pool:
                    total = await redis_pool.get(total_key) or 0
                    success = await redis_pool.get(success_key) or 0
                    failed = await redis_pool.get(failed_key) or 0
                    
                    stats.append({
                        "provider": provider,
                        "total_requests": int(total),
                        "successful_requests": int(success),
                        "failed_requests": int(failed),
                        "success_rate": round((int(success) / int(total) * 100) if int(total) > 0 else 0, 2)
                    })
            
            return stats
        except Exception as e:
            print(f"Error getting API stats: {e}")
            return []
    
    @staticmethod
    async def get_audit_logs(skip: int = 0, limit: int = 50) -> Dict:
        """Get admin audit logs"""
        try:
            total = await auth_db_module.db.audit_logs.count_documents({})
            logs = await auth_db_module.db.audit_logs.find({}).sort("timestamp", -1).skip(skip).limit(limit).to_list(length=limit)
            
            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])
            
            return {
                "total": total,
                "logs": logs,
                "page": skip // limit + 1,
                "pages": (total + limit - 1) // limit
            }
        except Exception as e:
            print(f"Error getting audit logs: {e}")
            return {"total": 0, "logs": [], "page": 1, "pages": 0}
    
    @staticmethod
    async def get_system_logs(skip: int = 0, limit: int = 100) -> Dict:
        """Get system event logs"""
        try:
            total = await auth_db_module.db.system_logs.count_documents({})
            logs = await auth_db_module.db.system_logs.find({}).sort("timestamp", -1).skip(skip).limit(limit).to_list(length=limit)
            
            for log in logs:
                log["_id"] = str(log["_id"])
            
            return {
                "total": total,
                "logs": logs,
                "page": skip // limit + 1,
                "pages": (total + limit - 1) // limit
            }
        except Exception as e:
            print(f"Error getting system logs: {e}")
            return {"total": 0, "logs": [], "page": 1, "pages": 0}
    
    @staticmethod
    def update_env_file(key: str, value: str) -> bool:
        """Update .env file with new API key"""
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
            
            # Read existing .env
            with open(env_path, "r") as f:
                lines = f.readlines()
            
            # Update or add the key
            key_found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    key_found = True
                    break
            
            if not key_found:
                lines.append(f"{key}={value}\n")
            
            # Write back to .env
            with open(env_path, "w") as f:
                f.writelines(lines)
            
            return True
        except Exception as e:
            print(f"Error updating .env file: {e}")
            return False

admin_services = AdminServices()

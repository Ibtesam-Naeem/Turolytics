#!/usr/bin/env python3
"""
Bouncie User Data Module
Handles user account information
"""

from typing import Dict, Any, Optional

class BouncieUserData:
    """Handles user data operations for Bouncie API."""
    
    def __init__(self, client):
        self.client = client
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get user account information."""
        return await self.client.get_user_info()
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """Get formatted user profile data."""
        user_result = await self.client.get_user_info()
        if not user_result["success"]:
            return user_result
        
        user_data = user_result["data"]
        
        return {
            "success": True,
            "data": {
                "profile": {
                    "id": user_data.get("id"),
                    "name": user_data.get("name"),
                    "email": user_data.get("email"),
                    "account_type": "Bouncie User"
                },
                "account_status": {
                    "active": True,
                    "authenticated": True
                }
            }
        }

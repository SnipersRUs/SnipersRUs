#!/usr/bin/env python3
"""
Simple Discord notifier for MMS trading system
Provides send_embed function for Discord webhook notifications
"""
import requests
import time
from typing import Dict, Optional

# Rate limiting for alerts
last_alert_times = {}
MAX_ALERTS_PER_HOUR = 20  # Default limit

def send_embed(webhook_url: str, embed_data: Dict, max_alerts_per_hour: int = MAX_ALERTS_PER_HOUR) -> bool:
    """
    Send embed to Discord webhook with rate limiting
    """
    if not webhook_url:
        return False
    
    # Rate limiting check
    current_time = time.time()
    hour_key = int(current_time // 3600)  # Hour bucket
    
    if hour_key not in last_alert_times:
        last_alert_times[hour_key] = 0
    
    if last_alert_times[hour_key] >= max_alerts_per_hour:
        return False  # Rate limited
    
    try:
        # Prepare payload
        payload = {
            "embeds": [embed_data]
        }
        
        # Send request
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 204:
            last_alert_times[hour_key] += 1
            return True
        else:
            print(f"Discord webhook error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Discord webhook error: {e}")
        return False














































#!/usr/bin/env python3
"""
Discord Integration for Enhanced MM Trading Bot
Handles all Discord webhook communications and alert formatting
"""
import aiohttp
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = None
        self.last_alert_times = {}  # Rate limiting
        self.alert_frequency_limit = 300  # 5 minutes between similar alerts
        self.setup_logging()

    def setup_logging(self):
        """Setup logging for Discord integration"""
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _can_send_alert(self, alert_type: str) -> bool:
        """Check if we can send an alert based on rate limiting"""
        current_time = time.time()
        last_time = self.last_alert_times.get(alert_type, 0)
        
        if current_time - last_time >= self.alert_frequency_limit:
            self.last_alert_times[alert_type] = current_time
            return True
        return False

    def _format_trade_alert(self, trade_data: Dict) -> Dict:
        """Format trade execution alert"""
        direction_emoji = "🟢" if trade_data.get('direction') == 'LONG' else "🔴"
        direction_color = 0x00ff00 if trade_data.get('direction') == 'LONG' else 0xff0000
        
        return {
            "embeds": [{
                "title": f"{direction_emoji} TRADE EXECUTED - {trade_data.get('symbol', 'N/A')}",
                "description": f"**Direction**: {trade_data.get('direction', 'N/A')}\n"
                             f"**Entry Price**: ${trade_data.get('entry_price', 0):.4f}\n"
                             f"**Stop Loss**: ${trade_data.get('stop_loss', 0):.4f}\n"
                             f"**Take Profits**: ${trade_data.get('take_profits', [0, 0, 0])[0]:.4f} | "
                             f"${trade_data.get('take_profits', [0, 0, 0])[1]:.4f} | "
                             f"${trade_data.get('take_profits', [0, 0, 0])[2]:.4f}\n"
                             f"**Risk/Reward**: {trade_data.get('risk_reward', 0):.2f}\n"
                             f"**Position Size**: ${trade_data.get('position_size', 0):.2f}\n"
                             f"**Leverage**: {trade_data.get('leverage', 1)}x\n"
                             f"**MM Confidence**: {trade_data.get('mm_confidence', 0):.0f}%\n"
                             f"**Setup Reason**: {trade_data.get('setup_reason', 'N/A')}",
                "color": direction_color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Enhanced MM Trading Bot"
                },
                "fields": [
                    {
                        "name": "MM Patterns",
                        "value": trade_data.get('mm_patterns', 'None detected'),
                        "inline": True
                    },
                    {
                        "name": "Volume Analysis",
                        "value": trade_data.get('volume_analysis', 'N/A'),
                        "inline": True
                    }
                ]
            }]
        }

    def _format_flush_alert(self, flush_data: Dict) -> Dict:
        """Format major flush alert"""
        flush_type = flush_data.get('type', 'UNKNOWN')
        strength = flush_data.get('strength', 0)
        
        if 'BEARISH' in flush_type:
            emoji = "🔴"
            color = 0xff6b6b
        elif 'BULLISH' in flush_type:
            emoji = "🟢"
            color = 0x4ecdc4
        else:
            emoji = "⚠️"
            color = 0xffa500
        
        return {
            "embeds": [{
                "title": f"{emoji} MAJOR FLUSH ALERT - {flush_data.get('symbol', 'N/A')}",
                "description": f"**Flush Type**: {flush_type}\n"
                             f"**Strength**: {strength:.0f}%\n"
                             f"**Price Change**: {flush_data.get('price_change', 0)*100:+.1f}%\n"
                             f"**Volume Spike**: {flush_data.get('volume_spike', 0):.1f}x\n"
                             f"**Trade Imbalance**: {flush_data.get('trade_imbalance', 0)}\n\n"
                             f"**⚠️ Potential Reversal Signal**",
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Enhanced MM Trading Bot - Flush Detection"
                }
            }]
        }

    def _format_mm_pattern_alert(self, pattern_data: Dict) -> Dict:
        """Format MM pattern detection alert"""
        pattern_type = pattern_data.get('type', 'UNKNOWN')
        confidence = pattern_data.get('confidence', 0)
        symbol = pattern_data.get('symbol', 'N/A')
        
        pattern_emojis = {
            'ICEBERG': '🧊',
            'SPOOFING': '🎭',
            'LAYERING': '📚',
            'DIVERGENCE': '🔄'
        }
        
        emoji = pattern_emojis.get(pattern_type, '🔍')
        
        return {
            "embeds": [{
                "title": f"{emoji} MM PATTERN DETECTED - {symbol}",
                "description": f"**Pattern**: {pattern_type}\n"
                             f"**Confidence**: {confidence:.0f}%\n"
                             f"**Details**: {pattern_data.get('details', 'N/A')}\n"
                             f"**Side**: {pattern_data.get('side', 'N/A')}",
                "color": 0x3498db,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Enhanced MM Trading Bot - Pattern Detection"
                }
            }]
        }

    def _format_portfolio_update(self, portfolio_data: Dict) -> Dict:
        """Format portfolio update alert"""
        balance = portfolio_data.get('balance', 0)
        unrealized_pnl = portfolio_data.get('unrealized_pnl', 0)
        total_balance = portfolio_data.get('total_balance', 0)
        daily_pnl = portfolio_data.get('daily_pnl', 0)
        
        pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
        pnl_color = 0x00ff00 if daily_pnl >= 0 else 0xff0000
        
        return {
            "embeds": [{
                "title": f"{pnl_emoji} PORTFOLIO UPDATE",
                "description": f"**Balance**: ${balance:,.2f}\n"
                             f"**Unrealized P&L**: ${unrealized_pnl:,.2f}\n"
                             f"**Total Balance**: ${total_balance:,.2f}\n"
                             f"**Daily P&L**: ${daily_pnl:,.2f}\n"
                             f"**Open Positions**: {portfolio_data.get('open_positions', 0)}\n"
                             f"**Total Trades**: {portfolio_data.get('total_trades', 0)}\n"
                             f"**Win Rate**: {portfolio_data.get('win_rate', 0):.1f}%",
                "color": pnl_color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Enhanced MM Trading Bot - Portfolio"
                }
            }]
        }

    async def send_alert(self, alert_type: str, data: Dict) -> bool:
        """Send alert to Discord"""
        if not self.webhook_url:
            self.logger.warning("No Discord webhook configured")
            return False
        
        if not self._can_send_alert(alert_type):
            self.logger.info(f"Rate limited: {alert_type}")
            return False
        
        try:
            # Format the alert based on type
            if alert_type == "trade_execution":
                payload = self._format_trade_alert(data)
            elif alert_type == "flush_alert":
                payload = self._format_flush_alert(data)
            elif alert_type == "mm_pattern":
                payload = self._format_mm_pattern_alert(data)
            elif alert_type == "portfolio_update":
                payload = self._format_portfolio_update(data)
            else:
                # Generic alert
                payload = {
                    "embeds": [{
                        "title": data.get('title', 'Alert'),
                        "description": data.get('description', 'No description'),
                        "color": data.get('color', 0x3498db),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }]
                }
            
            # Send to Discord
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 204:
                    self.logger.info(f"Alert sent successfully: {alert_type}")
                    return True
                else:
                    self.logger.error(f"Failed to send alert: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
            return False

    async def send_trade_alert(self, trade_data: Dict) -> bool:
        """Send trade execution alert"""
        return await self.send_alert("trade_execution", trade_data)

    async def send_flush_alert(self, flush_data: Dict) -> bool:
        """Send major flush alert"""
        return await self.send_alert("flush_alert", flush_data)

    async def send_mm_pattern_alert(self, pattern_data: Dict) -> bool:
        """Send MM pattern detection alert"""
        return await self.send_alert("mm_pattern", pattern_data)

    async def send_portfolio_update(self, portfolio_data: Dict) -> bool:
        """Send portfolio update alert"""
        return await self.send_alert("portfolio_update", portfolio_data)

    async def send_generic_alert(self, title: str, description: str, color: int = 0x3498db) -> bool:
        """Send generic alert"""
        data = {
            'title': title,
            'description': description,
            'color': color
        }
        return await self.send_alert("generic", data)

    async def test_webhook(self) -> bool:
        """Test Discord webhook connectivity"""
        try:
            test_data = {
                'title': '🧪 Webhook Test',
                'description': 'Discord webhook is working correctly!',
                'color': 0x00ff00
            }
            return await self.send_alert("test", test_data)
        except Exception as e:
            self.logger.error(f"Webhook test failed: {e}")
            return False

# Global Discord notifier instance
discord_notifier = None

async def get_discord_notifier(webhook_url: str) -> DiscordNotifier:
    """Get or create Discord notifier instance"""
    global discord_notifier
    if discord_notifier is None:
        discord_notifier = DiscordNotifier(webhook_url)
        await discord_notifier.__aenter__()
    return discord_notifier

async def cleanup_discord_notifier():
    """Cleanup Discord notifier"""
    global discord_notifier
    if discord_notifier:
        await discord_notifier.__aexit__(None, None, None)
        discord_notifier = None

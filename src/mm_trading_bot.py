#!/usr/bin/env python3
"""
Enhanced Market Maker Trading Bot
Integrates MM detection, trading system, and comprehensive monitoring
"""
import time
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

# Import our modules
from mm_detector import MMDetector, MarketState
from trading_system import TradingSystem, Position, TradeResult
from mm_config import config, DIV_TH, MM_CONF, EARLY_RR, USE_M15
from discord_integration import get_discord_notifier, cleanup_discord_notifier
from hourly_market_analyzer import HourlyMarketAnalyzer

class MMTradingBot:
    def __init__(self):
        self.detector = MMDetector()
        self.trading_system = TradingSystem()
        self.hourly_analyzer = HourlyMarketAnalyzer()
        self.discord_notifier = None
        self.setup_logging()
        
        # Bot state
        self.is_running = False
        self.scan_interval = 60  # 1 minute between scans
        self.last_scan_time = 0
        self.last_hourly_analysis = 0
        self.symbols_to_scan = config.symbols.priority_symbols
        
        # Performance tracking
        self.scan_count = 0
        self.signals_generated = 0
        self.trades_executed = 0
        self.alerts_sent = 0
        self.hourly_analyses_sent = 0
        
        # Load existing state
        self.trading_system.load_state()

    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mm_trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start the trading bot"""
        self.logger.info("Starting Enhanced MM Trading Bot...")
        self.is_running = True
        
        # Initialize Discord notifier
        if config.alerts.discord_webhook:
            self.discord_notifier = await get_discord_notifier(config.alerts.discord_webhook)
            # Test webhook
            await self.discord_notifier.test_webhook()
            
            # Initialize hourly analyzer with Discord notifier
            self.hourly_analyzer.discord_notifier = self.discord_notifier
        
        # Validate configuration
        issues = config.validate_config()
        if issues:
            self.logger.warning(f"Configuration issues: {issues}")
        
        # Print initial status
        self.print_status()
        
        try:
            while self.is_running:
                await self.run_cycle()
                await asyncio.sleep(self.scan_interval)
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Bot error: {e}")
        finally:
            await self.shutdown()

    async def run_cycle(self):
        """Run one complete trading cycle"""
        try:
            # Update existing positions
            current_prices = await self.get_current_prices()
            closed_trades = self.trading_system.update_positions(current_prices)
            
            if closed_trades:
                self.logger.info(f"Closed {len(closed_trades)} positions")
                for trade in closed_trades:
                    self.logger.info(f"Trade closed: {trade['symbol']} - {trade['reason']} - P&L: ${trade['pnl']:.2f}")
            
            # Scan for new opportunities
            if time.time() - self.last_scan_time >= self.scan_interval:
                await self.scan_markets()
                self.last_scan_time = time.time()
                self.scan_count += 1
            
            # Run hourly market analysis
            if time.time() - self.last_hourly_analysis >= 3600:  # Every hour
                await self.run_hourly_analysis()
                self.last_hourly_analysis = time.time()
                self.hourly_analyses_sent += 1
            
            # Save state periodically
            if self.scan_count % 10 == 0:  # Every 10 scans
                self.trading_system.save_state()
                self.print_status()
                
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")

    async def scan_markets(self):
        """Scan markets for MM opportunities"""
        self.logger.info("Scanning markets for MM opportunities...")
        
        for symbol in self.symbols_to_scan:
            try:
                # Get market data (this would be replaced with actual data source)
                spot_data, futures_data = await self.get_market_data(symbol)
                
                if not spot_data or not futures_data:
                    continue
                
                # Analyze MM activity
                market_state = self.detector.analyze_mm_activity(symbol, spot_data, futures_data)
                
                # Check for trading opportunities
                if self.should_execute_trade(market_state):
                    success = await self.execute_trade(market_state)
                    if success:
                        self.trades_executed += 1
                        self.logger.info(f"Trade executed for {symbol}")
                
                # Check for flush alerts
                flush_alert = self.detector.check_flush_alert(market_state)
                if flush_alert:
                    await self.send_alert(flush_alert)
                    self.alerts_sent += 1
                
                # Generate trading card if there's a setup
                if market_state.entry > 0 and market_state.risk_reward >= 1.2:
                    card = self.detector.create_trading_card(market_state)
                    self.logger.info(f"Trading card generated for {symbol}: {card.setup_reason}")
                
                self.signals_generated += 1
                
            except Exception as e:
                self.logger.error(f"Error scanning {symbol}: {e}")
            
            # Rate limiting
            await asyncio.sleep(0.1)

    async def run_hourly_analysis(self):
        """Run hourly market analysis and send to Discord"""
        try:
            self.logger.info("Running hourly market analysis...")
            
            # Generate market analysis
            market_analysis = await self.hourly_analyzer.analyze_all_symbols()
            
            # Generate volatility forecast
            volatility_forecast = await self.hourly_analyzer.predict_volatility()
            
            # Generate best trading times
            best_times = await self.hourly_analyzer.identify_best_trading_times()
            
            # Get trading status
            trading_status = self.get_trading_status()
            
            current_time = datetime.now(timezone.utc)
            
            # Send market update
            await self.hourly_analyzer.send_market_update(
                market_analysis, 
                volatility_forecast, 
                best_times, 
                trading_status,
                current_time
            )
            
            # Send portfolio card
            await self.hourly_analyzer.send_portfolio_card(trading_status, current_time)
            
            self.logger.info("Hourly market analysis completed and sent to Discord")
            
        except Exception as e:
            self.logger.error(f"Error in hourly analysis: {e}")

    def get_trading_status(self) -> Dict:
        """Get current trading system status"""
        portfolio = self.trading_system.get_portfolio_summary()
        positions = self.trading_system.get_trading_cards()
        
        return {
            'portfolio': portfolio,
            'positions': positions,
            'open_positions_count': len(positions),
            'total_trades': portfolio['total_trades'],
            'win_rate': portfolio['win_rate'],
            'daily_pnl': portfolio['daily_pnl'],
            'unrealized_pnl': portfolio['unrealized_pnl']
        }

    async def get_market_data(self, symbol: str) -> tuple:
        """Get market data for a symbol with realistic current prices"""
        # Current realistic prices (as of 2024)
        current_prices = {
            'BTC/USDT': 110000,  # Realistic BTC price over $100k
            'ETH/USDT': 3500,
            'SOL/USDT': 200,
            'BNB/USDT': 600,
            'XRP/USDT': 0.6,
            'ADA/USDT': 0.5,
            'DOGE/USDT': 0.15,
            'AVAX/USDT': 40
        }
        
        base_price = current_prices.get(symbol, 100)
        
        # Generate price history with some trend around realistic price
        prices = []
        current_price = base_price
        for i in range(100):
            # Add some volatility and trend
            change = np.random.normal(0, 0.02)  # 2% volatility
            trend = 0.001 if i > 50 else -0.001  # Slight trend change
            current_price *= (1 + change + trend)
            prices.append(current_price)
        
        # Generate volumes
        volumes = [np.random.uniform(1000, 10000) for _ in range(100)]
        
        # Generate trades
        trades = []
        for i in range(100):
            trades.append({
                'price': prices[i],
                'size': volumes[i],
                'side': 'buy' if np.random.random() > 0.5 else 'sell'
            })
        
        # Generate order book
        order_book = {
            'bids': [[prices[-1] * 0.999, np.random.uniform(100, 1000)] for _ in range(10)],
            'asks': [[prices[-1] * 1.001, np.random.uniform(100, 1000)] for _ in range(10)]
        }
        
        spot_data = {
            'prices': prices,
            'volumes': volumes,
            'trades': trades,
            'order_book': order_book
        }
        
        # Generate futures data
        futures_data = {
            'open_interest': [np.random.uniform(1000000, 5000000) for _ in range(20)],
            'funding_rate': np.random.uniform(-0.01, 0.01),
            'volumes': [np.random.uniform(100000, 1000000) for _ in range(20)]
        }
        
        return spot_data, futures_data

    async def get_current_prices(self) -> Dict[str, float]:
        """Get current prices for all open positions"""
        prices = {}
        for symbol in self.trading_system.positions.keys():
            try:
                # Get current price from market data
                spot_data, _ = await self.get_market_data(symbol)
                prices[symbol] = spot_data['prices'][-1]  # Use the last price from the generated data
            except Exception as e:
                self.logger.error(f"Error getting current price for {symbol}: {e}")
                # Fallback to realistic prices
                fallback_prices = {
                    'BTC/USDT': 105000,
                    'ETH/USDT': 3500,
                    'SOL/USDT': 200,
                    'BNB/USDT': 600,
                    'XRP/USDT': 0.6,
                    'ADA/USDT': 0.5,
                    'DOGE/USDT': 0.15,
                    'AVAX/USDT': 40
                }
                prices[symbol] = fallback_prices.get(symbol, 100)
        return prices

    def should_execute_trade(self, market_state: MarketState) -> bool:
        """Determine if we should execute a trade based on market state"""
        # Check if we can open a position
        if not self.trading_system.can_open_position(market_state.symbol):
            return False
        
        # Check MM activity
        if not market_state.mm_active or market_state.mm_confidence < MM_CONF:
            return False
        
        # Check setup quality
        if market_state.entry <= 0 or market_state.risk_reward < EARLY_RR:
            return False
        
        # Check bias alignment
        if not market_state.bias_aligned and market_state.setup_mode != "EARLY_M15":
            return False
        
        # Check for enhanced MM patterns
        has_mm_patterns = (market_state.iceberg_detected or 
                          market_state.spoofing_detected or 
                          market_state.layering_detected)
        
        if not has_mm_patterns and market_state.setup_mode == "EARLY_M15":
            return False
        
        return True

    async def execute_trade(self, market_state: MarketState) -> bool:
        """Execute a trade based on market state"""
        try:
            # Create trading card
            card = self.detector.create_trading_card(market_state)
            
            # Execute trade
            success = self.trading_system.open_position(
                symbol=market_state.symbol,
                direction=card.direction,
                entry_price=market_state.entry,
                stop_loss=market_state.stop_loss,
                take_profits=market_state.take_profit,
                mm_confidence=market_state.mm_confidence,
                setup_reason=card.setup_reason
            )
            
            if success:
                # Send trade alert via Discord
                if self.discord_notifier:
                    trade_data = {
                        'symbol': market_state.symbol,
                        'direction': card.direction,
                        'entry_price': market_state.entry,
                        'stop_loss': market_state.stop_loss,
                        'take_profits': market_state.take_profit,
                        'risk_reward': market_state.risk_reward,
                        'position_size': market_state.position_size,
                        'leverage': market_state.leverage,
                        'mm_confidence': market_state.mm_confidence,
                        'setup_reason': card.setup_reason,
                        'mm_patterns': self._format_mm_patterns(market_state.mm_patterns),
                        'volume_analysis': market_state.volume_profile
                    }
                    await self.discord_notifier.send_trade_alert(trade_data)
                    self.alerts_sent += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing trade for {market_state.symbol}: {e}")
            return False

    async def send_alert(self, alert: dict):
        """Send alert via Discord"""
        self.logger.info(f"ALERT: {alert['title']}")
        self.logger.info(f"Description: {alert['description']}")
        
        # Send to Discord if notifier is available
        if self.discord_notifier:
            try:
                await self.discord_notifier.send_generic_alert(
                    title=alert['title'],
                    description=alert['description'],
                    color=alert.get('color', 0x3498db)
                )
                self.alerts_sent += 1
            except Exception as e:
                self.logger.error(f"Failed to send Discord alert: {e}")

    def print_status(self):
        """Print current bot status"""
        portfolio = self.trading_system.get_portfolio_summary()
        
        print("\n" + "="*60)
        print("ENHANCED MM TRADING BOT STATUS")
        print("="*60)
        print(f"Balance: ${portfolio['balance']:.2f}")
        print(f"Unrealized P&L: ${portfolio['unrealized_pnl']:.2f}")
        print(f"Total Balance: ${portfolio['total_balance']:.2f}")
        print(f"Daily P&L: ${portfolio['daily_pnl']:.2f}")
        print(f"Max Drawdown: {portfolio['max_drawdown']:.2%}")
        print(f"Open Positions: {portfolio['open_positions']}")
        print(f"Total Trades: {portfolio['total_trades']}")
        print(f"Win Rate: {portfolio['win_rate']:.1f}%")
        print(f"Avg P&L: ${portfolio['avg_pnl']:.2f}")
        print("-"*60)
        print(f"Scans: {self.scan_count} | Signals: {self.signals_generated} | Trades: {self.trades_executed} | Alerts: {self.alerts_sent} | Hourly: {self.hourly_analyses_sent}")
        print("="*60)

    async def shutdown(self):
        """Shutdown the bot gracefully"""
        self.logger.info("Shutting down bot...")
        self.is_running = False
        
        # Save final state
        self.trading_system.save_state()
        
        # Cleanup Discord notifier
        if self.discord_notifier:
            await cleanup_discord_notifier()
        
        # Print final status
        self.print_status()
        
        self.logger.info("Bot shutdown complete")

    def get_trading_cards(self) -> List[dict]:
        """Get all current trading cards"""
        return self.trading_system.get_trading_cards()

    def _format_mm_patterns(self, mm_patterns: dict) -> str:
        """Format MM patterns for display"""
        patterns = []
        if mm_patterns.get('iceberg', {}).get('detected'):
            patterns.append("🧊 Iceberg")
        if mm_patterns.get('spoofing', {}).get('detected'):
            patterns.append("🎭 Spoofing")
        if mm_patterns.get('layering', {}).get('detected'):
            patterns.append("📚 Layering")
        if mm_patterns.get('flush', {}).get('detected'):
            patterns.append("💥 Flush")
        return " | ".join(patterns) if patterns else "None"

    def get_performance_metrics(self) -> dict:
        """Get comprehensive performance metrics"""
        portfolio = self.trading_system.get_portfolio_summary()
        
        return {
            "portfolio": portfolio,
            "bot_stats": {
                "scan_count": self.scan_count,
                "signals_generated": self.signals_generated,
                "trades_executed": self.trades_executed,
                "alerts_sent": self.alerts_sent,
                "uptime": time.time() - self.last_scan_time if self.last_scan_time > 0 else 0
            },
            "config": {
                "divergence_threshold": DIV_TH,
                "mm_confidence_threshold": MM_CONF,
                "early_min_rr": EARLY_RR,
                "m15_enabled": USE_M15
            }
        }

# Main execution
async def main():
    """Main function"""
    bot = MMTradingBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())

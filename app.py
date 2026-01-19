#!/usr/bin/env python3
"""
Trading Bot API Server
FastAPI-based REST API for controlling and monitoring the Bybit trading bot
Deployable on Railway
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
import os
import logging
from datetime import datetime, timezone
import uvicorn

from bybit_golden_pocket_bot import BybitGoldenPocketBot
from bybit_config import validate_config, BYBIT_CONFIG, BYBIT_TRADING_CONFIG

# Initialize FastAPI app
app = FastAPI(
    title="Bybit Trading Bot API",
    description="REST API for controlling and monitoring the Bybit Golden Pocket trading bot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
bot_instance = None
bot_task = None

# Request/Response models
class BotStatus(BaseModel):
    is_running: bool
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    active_trades: int
    daily_trades: int
    win_count: int
    loss_count: int
    last_trade_time: float

class TradeSignal(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    position_size: float
    leverage: int
    confidence: float
    reason: str

class AccountInfo(BaseModel):
    balance: Dict
    positions: List[Dict]
    active_trades: int
    daily_trades: int

class BotConfig(BaseModel):
    max_trades: int
    base_position_size: float
    leverage: int
    max_daily_trades: int
    paper_trading: bool

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    global bot_instance
    try:
        logger.info("🚀 Starting Trading Bot API Server...")
        
        # Validate configuration
        if not validate_config():
            logger.error("❌ Configuration validation failed")
            return
        
        # Initialize bot
        bot_instance = BybitGoldenPocketBot()
        logger.info("✅ Bot instance created successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global bot_task
    try:
        if bot_task:
            bot_task.cancel()
            logger.info("⏹️  Bot task cancelled")
        logger.info("🛑 API Server shutdown complete")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Bybit Trading Bot API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if bot_instance:
            # Test connection
            connection_ok = await bot_instance.test_connection()
            return {
                "status": "healthy" if connection_ok else "unhealthy",
                "connection": "connected" if connection_ok else "disconnected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "status": "unhealthy",
                "connection": "not_initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/status", response_model=BotStatus)
async def get_bot_status():
    """Get bot status and statistics"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        return BotStatus(
            is_running=bot_task is not None and not bot_task.done(),
            total_trades=bot_instance.total_trades,
            winning_trades=bot_instance.winning_trades,
            losing_trades=bot_instance.losing_trades,
            total_pnl=bot_instance.total_pnl,
            active_trades=len(bot_instance.active_trades),
            daily_trades=bot_instance.daily_trade_count,
            win_count=bot_instance.win_count,
            loss_count=bot_instance.loss_count,
            last_trade_time=bot_instance.last_trade_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/account", response_model=AccountInfo)
async def get_account_info():
    """Get account information"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        account_info = await bot_instance.get_account_info()
        return AccountInfo(**account_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config", response_model=BotConfig)
async def get_bot_config():
    """Get bot configuration"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        return BotConfig(
            max_trades=bot_instance.max_trades,
            base_position_size=bot_instance.base_position_size,
            leverage=bot_instance.leverage,
            max_daily_trades=bot_instance.max_daily_trades,
            paper_trading=BYBIT_CONFIG.get('testnet', True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/start")
async def start_bot(background_tasks: BackgroundTasks):
    """Start the trading bot"""
    global bot_task
    
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    if bot_task and not bot_task.done():
        raise HTTPException(status_code=400, detail="Bot is already running")
    
    try:
        # Start bot in background
        bot_task = asyncio.create_task(bot_instance.start())
        background_tasks.add_task(bot_task)
        
        logger.info("🚀 Bot started successfully")
        return {"message": "Bot started successfully", "status": "running"}
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
async def stop_bot():
    """Stop the trading bot"""
    global bot_task
    
    if not bot_task or bot_task.done():
        raise HTTPException(status_code=400, detail="Bot is not running")
    
    try:
        bot_task.cancel()
        logger.info("⏹️  Bot stopped successfully")
        return {"message": "Bot stopped successfully", "status": "stopped"}
        
    except Exception as e:
        logger.error(f"❌ Failed to stop bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scan")
async def run_scan():
    """Run a single scan cycle"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        await bot_instance.run_scan_cycle()
        return {"message": "Scan completed successfully"}
        
    except Exception as e:
        logger.error(f"❌ Scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trades")
async def get_active_trades():
    """Get active trades"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        return {
            "active_trades": bot_instance.active_trades,
            "count": len(bot_instance.active_trades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/symbols")
async def get_trading_symbols():
    """Get trading symbols"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        return {
            "symbols": bot_instance.trading_symbols,
            "count": len(bot_instance.trading_symbols)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a symbol"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        ticker = await bot_instance.exchange.get_ticker(symbol)
        klines = await bot_instance.exchange.get_klines(symbol, '1', 100)
        
        return {
            "symbol": symbol,
            "ticker": ticker,
            "klines": klines[-10:] if klines else []  # Last 10 candles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-connection")
async def test_connection():
    """Test connection to Bybit"""
    if not bot_instance:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        success = await bot_instance.test_connection()
        return {
            "connected": success,
            "message": "Connection successful" if success else "Connection failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(lines: int = 50):
    """Get recent log entries"""
    try:
        log_file = "bybit_bot.log"
        if not os.path.exists(log_file):
            return {"logs": [], "message": "No log file found"}
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

if __name__ == "__main__":
    # Get port from environment variable (Railway sets this)
    port = int(os.getenv("PORT", 8000))
    
    # Run the server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )

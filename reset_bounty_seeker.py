#!/usr/bin/env python3
"""
Reset Bounty Seeker Bot - Clear all trades and start fresh
"""
import sqlite3
import os

DB_PATH = "bounty_seeker_trades.db"

def reset_database():
    """Reset database to fresh state"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database {DB_PATH} not found")
        return False

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Clear all trades
        c.execute("DELETE FROM trades")
        print("✅ Cleared all trades")

        # Clear account state history (keep structure)
        c.execute("DELETE FROM account_state")
        print("✅ Cleared account state history")

        # Clear failed trades
        c.execute("DELETE FROM failed_trades")
        print("✅ Cleared failed trades list")

        # Insert fresh account state
        c.execute("""INSERT INTO account_state
                     (balance, starting_balance, total_trades, winning_trades, losing_trades, total_pnl, last_updated)
                     VALUES (1000.0, 1000.0, 0, 0, 0, 0.0, datetime('now'))""")
        print("✅ Reset account state: $1,000 balance, 0 wins, 0 losses")

        conn.commit()
        print("\n🎯 Database reset complete!")
        print("   Starting fresh: $1,000 balance")
        print("   0 wins, 0 losses")
        print("   All trades cleared")
        return True

    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    reset_database()



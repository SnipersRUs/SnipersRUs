#!/usr/bin/env python3
"""
Trade logging utilities for MMS
"""
import csv
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

def pnl_pct(side: str, entry: float, exit: float) -> float:
    """Calculate PnL percentage"""
    if side == "LONG":
        return ((exit - entry) / entry) * 100
    else:  # SHORT
        return ((entry - exit) / entry) * 100

def append_open(csv_path: str, open_row: Dict[str, Any]):
    """Append open trade to CSV"""
    try:
        file_exists = os.path.exists(csv_path)
        with open(csv_path, 'a', newline='') as f:
            fieldnames = ['ts_open', 'symbol', 'side', 'entry', 'tp1', 'tp2', 'stop', 'prob', 'rr', 'note']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(open_row)
    except Exception as e:
        print(f"Error appending open trade: {e}")

def append_close(csv_path: str, base_row: Dict[str, Any], close_data: Dict[str, Any]):
    """Append close data to existing open trade row"""
    try:
        # Read existing data
        rows = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        # Find and update the matching row
        for i, row in enumerate(rows):
            if (row.get('symbol') == base_row['symbol'] and
                row.get('ts_open') == str(base_row['ts_open'])):
                # Update the row with close data
                rows[i].update(close_data)
                break

        # Write back to file
        if rows:
            with open(csv_path, 'w', newline='') as f:
                fieldnames = list(rows[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
    except Exception as e:
        print(f"Error appending close data: {e}")

def update_stats(stats_path: str, base_row: Dict[str, Any], close_data: Dict[str, Any]):
    """Update trade statistics JSON file"""
    try:
        stats = {}
        if os.path.exists(stats_path):
            with open(stats_path, 'r') as f:
                stats = json.load(f)

        # Initialize counters if not exist
        if 'total_trades' not in stats:
            stats['total_trades'] = 0
        if 'wins' not in stats:
            stats['wins'] = 0
        if 'losses' not in stats:
            stats['losses'] = 0
        if 'total_pnl' not in stats:
            stats['total_pnl'] = 0.0
        if 'win_rate' not in stats:
            stats['win_rate'] = 0.0

        # Update stats
        stats['total_trades'] += 1
        if close_data['outcome'].startswith('WIN'):
            stats['wins'] += 1
        else:
            stats['losses'] += 1

        stats['total_pnl'] += close_data['pnl_pct']
        stats['win_rate'] = (stats['wins'] / stats['total_trades']) * 100 if stats['total_trades'] > 0 else 0

        # Add last trade info
        stats['last_trade'] = {
            'symbol': base_row['symbol'],
            'side': base_row['side'],
            'outcome': close_data['outcome'],
            'pnl_pct': close_data['pnl_pct'],
            'timestamp': close_data['ts_close']
        }

        # Save updated stats
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        print(f"Error updating stats: {e}")

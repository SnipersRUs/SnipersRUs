#!/usr/bin/env python3
"""
Moon Cycles BTC Analyzer
Analyzes correlation between moon phases and Bitcoin price movements
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
from collections import defaultdict

class MoonPhaseCalculator:
    """Calculate moon phases using same algorithm as Pine Script"""

    @staticmethod
    def get_jd(year: int, month: int, day: int) -> float:
        """Calculate Julian Date"""
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        jd_int = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        return float(jd_int)

    @staticmethod
    def fmod(value: float, modulus: float) -> float:
        """Floating point modulo"""
        return value - (value // modulus) * modulus

    @staticmethod
    def deg2rad(degrees: float) -> float:
        """Convert degrees to radians"""
        return degrees * np.pi / 180

    @staticmethod
    def get_new_moon_jd(k: float) -> float:
        """Calculate New Moon Julian Date using Meeus algorithm"""
        T = k / 1236.85
        JDE = 2451550.09766 + 29.530588861 * k + 0.00015437 * (T**2) - 0.000000150 * (T**3) + 0.00000000073 * (T**4)
        E = 1 - 0.002516 * T - 0.0000074 * (T**2)

        M_deg = MoonPhaseCalculator.fmod(2.5534 + 29.10535670 * k - 0.0000014 * (T**2) - 0.00000011 * (T**3), 360)
        M = MoonPhaseCalculator.deg2rad(M_deg)

        Mprime_deg = MoonPhaseCalculator.fmod(201.5643 + 385.81693528 * k + 0.0107582 * (T**2) + 0.00001238 * (T**3) - 0.000000058 * (T**4), 360)
        Mprime = MoonPhaseCalculator.deg2rad(Mprime_deg)

        F_deg = MoonPhaseCalculator.fmod(160.7108 + 390.67050284 * k - 0.0016118 * (T**2) - 0.00000227 * (T**3) + 0.000000011 * (T**4), 360)
        F = MoonPhaseCalculator.deg2rad(F_deg)

        Omega_deg = MoonPhaseCalculator.fmod(124.7746 - 1.5635 * T + 0.0020672 * (T**2) + 0.00000215 * (T**3), 360)
        Omega = MoonPhaseCalculator.deg2rad(Omega_deg)

        correction = (-0.40720 * np.sin(Mprime) + 0.17241 * E * np.sin(M) +
                      0.01608 * np.sin(2 * Mprime) + 0.01039 * np.sin(2 * F) +
                      0.00739 * E * np.sin(Mprime - M) - 0.00514 * E * np.sin(Mprime + M) +
                      0.00208 * E * E * np.sin(2 * M) - 0.00111 * np.sin(Mprime - 2 * F) -
                      0.00057 * np.sin(Mprime + 2 * F) + 0.00056 * E * np.sin(2 * Mprime + M) -
                      0.00042 * np.sin(3 * Mprime) + 0.00042 * E * np.sin(M + 2 * F) +
                      0.00038 * E * np.sin(M - 2 * F) - 0.00024 * E * np.sin(2 * Mprime - M) -
                      0.00017 * np.sin(Omega) - 0.00007 * np.sin(Mprime + 2 * M) +
                      0.00004 * np.sin(2 * Mprime - 2 * F) + 0.00004 * np.sin(3 * M) +
                      0.00003 * np.sin(Mprime + M - 2 * F) + 0.00003 * np.sin(2 * Mprime + 2 * F) -
                      0.00003 * np.sin(Mprime + M + 2 * F) + 0.00003 * np.sin(Mprime - M + 2 * F) -
                      0.00002 * np.sin(Mprime - M - 2 * F) - 0.00002 * np.sin(3 * Mprime + M) +
                      0.00002 * np.sin(4 * Mprime))

        return JDE + correction

    @staticmethod
    def get_moon_phase(date: datetime) -> Tuple[float, str]:
        """Get moon phase for a given date. Returns (phase, phase_name)"""
        year, month, day = date.year, date.month, date.day
        current_jd = MoonPhaseCalculator.get_jd(year, month, day)

        decimal_year = year + (month - 0.5) / 12.0
        k = int((decimal_year - 2000) * 12.3685)

        jd_new = MoonPhaseCalculator.get_new_moon_jd(k)
        jd_new_prev = MoonPhaseCalculator.get_new_moon_jd(k - 1)
        jd_new_next = MoonPhaseCalculator.get_new_moon_jd(k + 1)

        if jd_new > current_jd:
            last_jd = jd_new_prev
            next_jd = jd_new
        else:
            last_jd = jd_new
            next_jd = jd_new_next

        phase = (current_jd - last_jd) / (next_jd - last_jd)

        # Classify phase
        if phase < 0.03 or phase > 0.97:
            return phase, "New Moon"
        elif phase > 0.47 and phase < 0.53:
            return phase, "Full Moon"
        elif phase > 0.22 and phase < 0.28:
            return phase, "First Quarter"
        elif phase > 0.72 and phase < 0.78:
            return phase, "Last Quarter"
        elif phase < 0.5:
            return phase, "Waxing"
        else:
            return phase, "Waning"


class BTCMoonAnalyzer:
    """Analyze BTC price movements correlated with moon phases"""

    def __init__(self):
        self.moon_calc = MoonPhaseCalculator()

    def fetch_btc_data(self, days: int = 365) -> pd.DataFrame:
        """Fetch BTC daily data from CoinGecko API"""
        print(f"Fetching {days} days of BTC data...")

        try:
            # CoinGecko API endpoint
            url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Convert to DataFrame
            prices = data['prices']
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('date')
            df = df[['price']]

            # Calculate daily returns
            df['return'] = df['price'].pct_change()
            df['return_pct'] = df['return'] * 100

            # Calculate forward returns (next 1, 3, 7 days)
            df['return_1d'] = df['price'].pct_change(1).shift(-1) * 100
            df['return_3d'] = df['price'].pct_change(3).shift(-3) * 100
            df['return_7d'] = df['price'].pct_change(7).shift(-7) * 100

            # Calculate volatility
            df['volatility'] = df['return'].rolling(7).std() * 100

            print(f"✓ Fetched {len(df)} days of data")
            return df

        except Exception as e:
            print(f"Error fetching data: {e}")
            print("Using sample data instead...")
            # Return sample data structure
            return pd.DataFrame()

    def add_moon_phases(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add moon phase information to DataFrame"""
        print("Calculating moon phases...")

        phases = []
        phase_names = []

        for date in df.index:
            phase, phase_name = self.moon_calc.get_moon_phase(date.to_pydatetime())
            phases.append(phase)
            phase_names.append(phase_name)

        df['moon_phase'] = phases
        df['moon_phase_name'] = phase_names

        print(f"✓ Calculated moon phases for {len(df)} days")
        return df

    def analyze_phase_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate statistics for each moon phase"""
        print("\nAnalyzing moon phase correlations...")

        stats = {}
        phase_groups = df.groupby('moon_phase_name')

        for phase_name, group in phase_groups:
            if len(group) < 5:  # Skip if too few samples
                continue

            stats[phase_name] = {
                'count': len(group),
                'avg_return_1d': group['return_1d'].mean(),
                'avg_return_3d': group['return_3d'].mean(),
                'avg_return_7d': group['return_7d'].mean(),
                'win_rate_1d': (group['return_1d'] > 0).sum() / len(group) * 100,
                'win_rate_3d': (group['return_3d'] > 0).sum() / len(group) * 100,
                'win_rate_7d': (group['return_7d'] > 0).sum() / len(group) * 100,
                'avg_volatility': group['volatility'].mean(),
                'max_gain_7d': group['return_7d'].max(),
                'max_loss_7d': group['return_7d'].min(),
            }

        return stats

    def print_report(self, stats: Dict):
        """Print formatted analysis report"""
        print("\n" + "="*80)
        print("MOON PHASES vs BITCOIN PRICE - STATISTICAL ANALYSIS")
        print("="*80)

        for phase_name, data in sorted(stats.items()):
            print(f"\n{'🌑' if 'New' in phase_name else '🌕' if 'Full' in phase_name else '🌓'} {phase_name}")
            print("-" * 60)
            print(f"  Sample Size:        {data['count']} days")
            print(f"  Avg Return (1d):    {data['avg_return_1d']:+.2f}%")
            print(f"  Avg Return (3d):    {data['avg_return_3d']:+.2f}%")
            print(f"  Avg Return (7d):    {data['avg_return_7d']:+.2f}%")
            print(f"  Win Rate (1d):      {data['win_rate_1d']:.1f}%")
            print(f"  Win Rate (3d):      {data['win_rate_3d']:.1f}%")
            print(f"  Win Rate (7d):      {data['win_rate_7d']:.1f}%")
            print(f"  Avg Volatility:     {data['avg_volatility']:.2f}%")
            print(f"  Best 7d Gain:       {data['max_gain_7d']:+.2f}%")
            print(f"  Worst 7d Loss:     {data['max_loss_7d']:+.2f}%")

        print("\n" + "="*80)
        print("KEY INSIGHTS:")
        print("="*80)

        # Find best performing phases
        best_7d = max(stats.items(), key=lambda x: x[1]['avg_return_7d'])
        worst_7d = min(stats.items(), key=lambda x: x[1]['avg_return_7d'])
        best_winrate = max(stats.items(), key=lambda x: x[1]['win_rate_7d'])

        print(f"\n✓ Best 7-Day Returns: {best_7d[0]} ({best_7d[1]['avg_return_7d']:+.2f}%)")
        print(f"✓ Worst 7-Day Returns: {worst_7d[0]} ({worst_7d[1]['avg_return_7d']:+.2f}%)")
        print(f"✓ Highest Win Rate (7d): {best_winrate[0]} ({best_winrate[1]['win_rate_7d']:.1f}%)")

        print("\n⚠️  DISCLAIMER: Correlation does not imply causation.")
        print("   Moon phases are one of many factors. Always use proper risk management.")
        print("="*80)

    def save_results(self, df: pd.DataFrame, stats: Dict, filename: str = "moon_cycles_btc_analysis.json"):
        """Save analysis results to JSON"""
        output = {
            'analysis_date': datetime.now().isoformat(),
            'total_days_analyzed': len(df),
            'date_range': {
                'start': df.index.min().isoformat(),
                'end': df.index.max().isoformat()
            },
            'phase_statistics': stats,
            'summary': {
                'phases_found': list(stats.keys()),
                'total_samples': sum(s['count'] for s in stats.values())
            }
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✓ Results saved to {filename}")


def main():
    """Run the analysis"""
    analyzer = BTCMoonAnalyzer()

    # Fetch BTC data (last 365 days by default)
    df = analyzer.fetch_btc_data(days=365)

    if df.empty:
        print("❌ Could not fetch data. Please check your internet connection.")
        return

    # Add moon phases
    df = analyzer.add_moon_phases(df)

    # Calculate statistics
    stats = analyzer.analyze_phase_stats(df)

    # Print report
    analyzer.print_report(stats)

    # Save results
    analyzer.save_results(df, stats)

    print("\n✓ Analysis complete!")


if __name__ == "__main__":
    main()

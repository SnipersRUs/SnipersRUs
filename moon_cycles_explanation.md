# Moon Cycles Indicator - How It Works

## 🔬 Technical Explanation

### 1. **Julian Date Calculation**
- Converts current date (year, month, day) to Julian Date (JD)
- JD is a continuous count of days since January 1, 4713 BC
- Used for precise astronomical calculations

### 2. **Lunation Number (k)**
- Calculates which moon cycle we're in since year 2000
- Formula: `k = floor((decimal_year - 2000) * 12.3685)`
- ~12.37 lunations per year (29.5 days each)

### 3. **New Moon Calculation (Meeus Algorithm)**
- Uses Jean Meeus's astronomical algorithm for precise new moon timing
- Calculates:
  - **T**: Time in Julian centuries
  - **JDE**: Julian Ephemeris Day (base new moon time)
  - **E**: Earth's eccentricity correction
  - **M, M', F, Ω**: Mean anomaly, lunar anomaly, argument of latitude, lunar node
- Applies 60+ correction terms for accuracy

### 4. **Phase Calculation**
- Finds last and next new moon dates
- Calculates current phase: `phase = (current_jd - last_jd) / (next_jd - last_jd)`
- Phase values:
  - **0.0** = New Moon 🌑
  - **0.25** = First Quarter 🌓
  - **0.5** = Full Moon 🌕
  - **0.75** = Last Quarter 🌗

### 5. **Phase Detection Windows**
- **New Moon**: `phase < 0.03 OR phase > 0.97` (±1 day window)
- **Full Moon**: `phase > 0.47 AND phase < 0.53` (±3 day window)
- **First Quarter**: `phase > 0.22 AND phase < 0.28`
- **Last Quarter**: `phase > 0.72 AND phase < 0.78`

### 6. **Visualization**
- Only plots markers on day changes (not every bar)
- Background color changes during new/full moon periods
- Phase value plotted in data window (0-1 range)

## 📊 What This Measures

The indicator tracks **lunar gravitational cycles** which some traders believe correlate with:
- Market sentiment shifts
- Volume patterns
- Reversal points
- Volatility spikes

## 🎯 Key Features

1. **Astronomical Accuracy**: Uses Meeus algorithm (same as NASA)
2. **Performance Optimized**: Caches calculations, only recalculates on day changes
3. **Precise Timing**: Down to day-level accuracy
4. **Visual Clarity**: Clear markers for each moon phase

## ⚠️ Important Notes

- This is a **correlation indicator**, not a causation predictor
- Moon phases don't directly cause market movements
- Useful for pattern recognition, not guaranteed signals
- Always combine with other technical analysis

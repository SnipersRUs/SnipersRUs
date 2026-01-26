// ============================================
console.log('[DEBUG] Script block started');
// OKX REAL-TIME DATA
// ============================================
const OKX_WS_URL = 'wss://ws.okx.com:8443/ws/v5/public';
const OKX_BASE_URL = 'https://www.okx.com/api/v5/market';

let state = {
    symbol: 'BTC',
    instId: 'BTC-USDT-SWAP',
    tvSymbol: 'OKX:BTCUSDT.P',
    price: null,
    prices: [],
    volume: [],
    lastPrice: null,
    pct24h: null,
    priceHistory: [],
    support: null,
    resistance: null,
    trend: 'NEUTRAL',
    trend4H: 'NEUTRAL', // 4HR trend (persistent, doesn't change on every tick)
    priceHistory4H: [], // Stores prices for 4HR trend calculation
    last4HCandleTime: null, // Track when last 4HR candle was formed
    volume24h: null,
    lastUpdate: null,
    lastRenderTime: 0,
    lastRenderPrice: null,
    lastDirection: null,
    nextScanAt: null,
    dailyHigh: null,
    dailyLow: null,
    dailyGpHigh: null,
    dailyGpLow: null,
    weeklyGpHigh: null,
    weeklyGpLow: null,
    divergenceState: 'NONE',
    divergenceLastUpdate: 0,
    theme: 'dark'
};

let ws = null;
let reconnectTimer = null;
let restPollTimer = null;
let staleCheckTimer = null;
let pairSelectEl = null;
let signalHistory = [];

// ============================================
// DISCORD & USER UTILS
// ============================================
const DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1463740804219670548/DOjU_kIJbl2eQ7SKYmPuSClfXj24y3JVJhOCaCPNolsomPBhXlWcgADwSRLgJnyD1KVY';

async function sendToDiscord(payload) {
    if (!DISCORD_WEBHOOK_URL) return;
    try {
        await fetch(DISCORD_WEBHOOK_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch (e) {
        console.error('Discord Webhook Error:', e);
    }
}

function getUsername() {
    return localStorage.getItem('srus_username') || 'Anonymous Sniper';
}

function setUsername() {
    const current = getUsername();
    const name = prompt('Enter your Display Name for the Leaderboard:', current === 'Anonymous Sniper' ? '' : current);
    if (name && name.trim()) {
        localStorage.setItem('srus_username', name.trim());
        updateProfileUI();
    }
}

function updateProfileUI() {
    const name = getUsername();
    const nameEl = document.getElementById('userProfileName');
    if (nameEl) nameEl.textContent = name;
}

// ============================================
// OKX WEBSOCKET CONNECTION
// ============================================
function connectOKX() {
    try {
        if (ws) {
            ws.close();
        }
        console.log('[DEBUG] Connecting to OKX WebSocket:', OKX_WS_URL);
        ws = new WebSocket(OKX_WS_URL);

        ws.onopen = function () {
            console.log('✅ Connected to OKX WebSocket');
            updateConnectionStatus(true);

            // Subscribe to BTC-USDT perpetual trades + ticker
            const subscribeMsg = {
                op: 'subscribe',
                args: [{
                    channel: 'trades',
                    instId: state.instId
                }, {
                    channel: 'tickers',
                    instId: state.instId
                }]
            };
            ws.send(JSON.stringify(subscribeMsg));
            console.log('[DEBUG] Subscribed to:', subscribeMsg);

            // Cancel reconnect timer
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
        };

        ws.onmessage = function (event) {
            try {
                const payload = JSON.parse(event.data);
                if (!payload || !payload.data || !payload.data[0]) return;

                const message = payload.data[0];
                const channel = payload.arg && payload.arg.channel;

                if (channel === 'trades') {
                    const price = parseFloat(message.px);
                    const volume = parseFloat(message.sz);
                    if (!Number.isNaN(price) && !Number.isNaN(volume)) {
                        updateMarket(price, volume);
                    }
                } else if (channel === 'tickers') {
                    const price = parseFloat(message.last);
                    const open24h = parseFloat(message.open24h);
                    const volume24h = parseFloat(message.volCcy24h);
                    state.volume24h = Number.isNaN(volume24h) ? state.volume24h : volume24h;
                    if (!Number.isNaN(price) && !Number.isNaN(open24h) && open24h > 0) {
                        state.pct24h = ((price - open24h) / open24h) * 100;
                    }
                    if (!Number.isNaN(price)) {
                        updateMarket(price, 0);
                    }
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onclose = function (event) {
            console.log('❌ OKX WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
            updateConnectionStatus(false);

            // Reconnect after 5 seconds
            reconnectTimer = setTimeout(() => {
                console.log('🔄 Reconnecting to OKX...');
                connectOKX();
            }, 5000);
        };

        ws.onerror = function (error) {
            console.error('❌ OKX WebSocket error:', error);
            updateConnectionStatus(false);
        };
    } catch (error) {
        console.error('Failed to connect to OKX:', error);
        updateConnectionStatus(false);
    }
}

// ============================================
// MARKET UPDATE LOGIC
// ============================================
function updateMarket(price, volume) {
    state.price = price;
    state.lastUpdate = Date.now();
    // Update price state
    state.prices.push(price);
    state.volume.push(volume);
    state.priceHistory.push({ ts: Date.now(), price });

    // Keep last 200 candles
    if (state.prices.length > 200) {
        state.prices.shift();
        state.volume.shift();
    }

    // Keep last 36 hours of price history
    const cutoff = Date.now() - (36 * 60 * 60 * 1000);
    if (state.priceHistory.length > 0 && state.priceHistory[0].ts < cutoff) {
        state.priceHistory = state.priceHistory.filter(p => p.ts >= cutoff);
    }

    // Calculate price change (prefer 24h change)
    let pctChange = null;
    if (typeof state.pct24h === 'number') {
        pctChange = state.pct24h;
    } else if (state.lastPrice) {
        const change = price - state.lastPrice;
        pctChange = (change / state.lastPrice * 100);
    } else {
        pctChange = 0;
    }
    updatePriceDisplay(price, pctChange);

    state.lastPrice = price;

    // Calculate support/resistance (min/max of last 50 prices)
    const recentPrices = state.prices.slice(-50);
    state.support = Math.min(...recentPrices) * 0.999;
    state.resistance = Math.max(...recentPrices) * 1.001;

    // Calculate 4HR trend (only update when a new 4HR candle would form)
    const now = Date.now();
    const fourHours = 4 * 60 * 60 * 1000; // 4 hours in milliseconds
    const shouldUpdate4HTrend = !state.last4HCandleTime || (now - state.last4HCandleTime) >= fourHours;

    // Store price for 4HR trend calculation
    state.priceHistory4H.push({ ts: now, price: price });

    // Keep only last 50 entries for 4HR trend
    if (state.priceHistory4H.length > 50) {
        state.priceHistory4H.shift();
    }

    // Update 4HR trend only when a new 4HR candle would form (every 4 hours)
    if (shouldUpdate4HTrend && state.priceHistory4H.length >= 10) {
        // Compare current price to price from ~4 hours ago
        const currentPrice = state.priceHistory4H[state.priceHistory4H.length - 1].price;
        const pastPrice = state.priceHistory4H[Math.max(0, state.priceHistory4H.length - 10)].price;
        const diff = currentPrice - pastPrice;

        // Threshold to prevent jittering on noise (0.1% change)
        if (diff > (pastPrice * 0.001)) {
            state.trend4H = 'BULLISH';
        } else if (diff < -(pastPrice * 0.001)) {
            state.trend4H = 'BEARISH';
        } else {
            // Keep previous trend if noise (only set to neutral if it was already neutral)
            if (state.trend4H === 'NEUTRAL') state.trend4H = 'NEUTRAL';
        }

        state.last4HCandleTime = now;
    }

    // Use 4HR trend for display
    state.trend = state.trend4H;

    // Update UI
    updateMarketInfo();
}


const priceFormatter = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
});

// Track last signal sent to Discord to prevent duplicates (per symbol)
const signalSentTimes = new Map();
let lastWatchlistHash = null;

const formatSignalPrice = (val) => {
    if (!val) return '0.00';
    const num = Number(val);
    if (num < 1.0) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 8,
            maximumFractionDigits: 8
        }).format(num);
    }
    return priceFormatter.format(num);
};

function updatePriceDisplay(price, pctChange) {
    const priceEl = document.getElementById('btcPrice');
    const changeEl = document.getElementById('btcChange');

    if (!priceEl) {
        console.error('[ERROR] btcPrice element not found');
        return;
    }

    const now = Date.now();
    const shouldRender = !state.lastRenderTime || now - state.lastRenderTime > 500;
    const significantMove = !state.lastRenderPrice || Math.abs(price - state.lastRenderPrice) >= 0.5;

    if (!shouldRender && !significantMove) return;

    try {
        priceEl.textContent = `$${priceFormatter.format(price)}`;
        priceEl.style.opacity = '1';
    } catch (error) {
        console.error('[ERROR] Failed to format price:', error, price);
    }

    if (changeEl) {
        const pctStr = `${pctChange >= 0 ? '+' : ''}${pctChange.toFixed(2)}%`;
        changeEl.textContent = pctStr;
        // Bearish is purple, bullish is green
        changeEl.className = `price-change ${pctChange >= 0 ? 'change-positive' : 'change-negative'}`;
    }

    const direction = pctChange >= 0 ? 'up' : 'down';
    state.lastDirection = direction;

    state.lastRenderTime = now;
    state.lastRenderPrice = price;

    // Update paper trading market price if it exists
    try {
        if (typeof window.calculatePaperOrder === 'function') {
            window.calculatePaperOrder();
        }
    } catch (error) {
        console.error('[ERROR] Failed to update paper order:', error);
    }

    // Update active trades P&L when price changes
    try {
        if (typeof renderActiveTrades === 'function' && Object.keys(activeTrades).length > 0) {
            renderActiveTrades();
        }
    } catch (error) {
        console.error('[ERROR] Failed to update active trades:', error);
    }
}

function calculateRsi(prices, period = 14) {
    if (prices.length < period + 1) return null;
    let gains = 0;
    let losses = 0;
    for (let i = prices.length - period; i < prices.length; i++) {
        const change = prices[i] - prices[i - 1];
        if (change >= 0) gains += change;
        else losses -= change;
    }
    if (losses === 0) return 100;
    const rs = gains / losses;
    return 100 - (100 / (1 + rs));
}

function calculateMoneyFlow(prices, volumes, period = 14) {
    if (prices.length < period + 1 || volumes.length < period) return null;
    let positive = 0;
    let negative = 0;
    for (let i = prices.length - period; i < prices.length; i++) {
        const change = prices[i] - prices[i - 1];
        const vol = volumes[i - 1] || 0;
        if (change >= 0) positive += vol;
        else negative += vol;
    }
    if (negative === 0) return 100;
    return (100 * positive) / (positive + negative);
}

function updateMarketInfo() {
    if (!state.price) return;

    const trendEl = document.getElementById('marketTrend');
    if (trendEl) {
        // Use 4HR trend for display
        trendEl.textContent = state.trend4H || state.trend || 'NEUTRAL';
        trendEl.className = `info-value ${(state.trend4H || state.trend) === 'BULLISH' ? 'value-up' : (state.trend4H || state.trend) === 'BEARISH' ? 'value-down' : 'value-neutral'}`;
    }

    document.getElementById('supportLevel').textContent = state.support ? `$${state.support.toFixed(2)}` : '--';
    document.getElementById('resistanceLevel').textContent = state.resistance ? `$${state.resistance.toFixed(2)}` : '--';

    // Volume
    const recentVolume = state.volume.slice(-20);
    const avgVolume = recentVolume.length > 0 ? recentVolume.reduce((a, b) => a + b, 0) / recentVolume.length : 0;
    const lastVolume = state.volume[state.volume.length - 1] || 0;
    const volMultiplier = avgVolume > 0 ? lastVolume / avgVolume : 0;

    const volEl = document.getElementById('volumeLevel');
    if (state.volume24h) {
        const volumeMillions = (state.volume24h / 1_000_000).toFixed(1);
        volEl.textContent = `${volumeMillions}M`;
        volEl.className = 'info-value value-neutral';
    } else {
        volEl.textContent = '--';
        volEl.className = 'info-value value-neutral';
    }

    const rvolEl = document.getElementById('rvolStatus');
    if (volMultiplier > 2.0) {
        rvolEl.textContent = 'HIGH (3x)';
        rvolEl.className = 'info-value value-up';
    } else if (volMultiplier > 1.5) {
        rvolEl.textContent = 'ELEVATED';
        rvolEl.className = 'info-value value-neutral';
    } else {
        rvolEl.textContent = 'NORMAL';
        rvolEl.className = 'info-value value-neutral';
    }

    const rsi = calculateRsi(state.prices, 14);
    const moneyFlow = calculateMoneyFlow(state.prices, state.volume, 14);
    const nearSupport = state.support && Math.abs(state.price - state.support) / state.price < 0.003;
    const nearResistance = state.resistance && Math.abs(state.price - state.resistance) / state.price < 0.003;

    const gpsEl = document.getElementById('gpsStatus');
    if (state.dailyGpHigh && state.dailyGpLow) {
        gpsEl.textContent = `${priceFormatter.format(state.dailyGpLow)} - ${priceFormatter.format(state.dailyGpHigh)}`;
        gpsEl.className = 'info-value value-neutral';
    } else {
        gpsEl.textContent = '--';
        gpsEl.className = 'info-value value-neutral';
    }

    const divEl = document.getElementById('divergenceStatus');
    const now = Date.now();
    let nextState = 'NONE';
    if (rsi !== null && rsi < 30) nextState = 'BULLISH (RSI)';
    if (rsi !== null && rsi > 70) nextState = 'BEARISH (RSI)';

    if (nextState !== state.divergenceState || now - state.divergenceLastUpdate > 5000) {
        state.divergenceState = nextState;
        state.divergenceLastUpdate = now;
    }

    if (state.divergenceState === 'BULLISH (RSI)') {
        divEl.textContent = state.divergenceState;
        divEl.className = 'info-value value-up';
    } else if (state.divergenceState === 'BEARISH (RSI)') {
        divEl.textContent = state.divergenceState;
        divEl.className = 'info-value value-down';
    } else {
        divEl.textContent = 'NONE';
        divEl.className = 'info-value value-neutral';
    }

    updateDistanceBadges();
}

function updateDistanceBadges() {
    const gpsDistanceEl = document.getElementById('gpsDistance');
    const supportDistanceEl = document.getElementById('supportDistance');
    const resistanceDistanceEl = document.getElementById('resistanceDistance');
    const dailyGpDistanceEl = document.getElementById('dailyGpDistance');
    const liquidityDistanceEl = document.getElementById('liquidityDistance');

    if (!state.price || !state.support || !state.resistance) return;
    const supportDistPct = ((state.price - state.support) / state.price) * 100;
    const resistanceDistPct = ((state.resistance - state.price) / state.price) * 100;
    const gpsDist = Math.min(Math.abs(supportDistPct), Math.abs(resistanceDistPct));

    gpsDistanceEl.textContent = `${gpsDist.toFixed(2)}%`;
    supportDistanceEl.textContent = `${supportDistPct.toFixed(2)}%`;
    resistanceDistanceEl.textContent = `${resistanceDistPct.toFixed(2)}%`;

    if (state.dailyGpHigh && state.dailyGpLow) {
        const inDailyGp = state.price >= state.dailyGpLow && state.price <= state.dailyGpHigh;
        if (inDailyGp) {
            if (dailyGpDistanceEl) dailyGpDistanceEl.textContent = 'INSIDE GP';
        } else {
            const distToGp = state.price < state.dailyGpLow
                ? ((state.dailyGpLow - state.price) / state.price) * 100
                : ((state.price - state.dailyGpHigh) / state.price) * 100;
            if (dailyGpDistanceEl) dailyGpDistanceEl.textContent = `${distToGp.toFixed(2)}%`;
        }
    } else {
        if (dailyGpDistanceEl) dailyGpDistanceEl.textContent = '--';
    }

    const nearestLevel = Math.abs(supportDistPct) <= Math.abs(resistanceDistPct)
        ? state.support
        : state.resistance;
    if (liquidityDistanceEl) liquidityDistanceEl.textContent = priceFormatter.format(nearestLevel);

    // Update GPS popup values
    updateGpsPopup();
}

function updateGpsPopup() {
    const currentPriceEl = document.getElementById('gpsCurrentPrice');
    const dailyHighEl = document.getElementById('gpsDailyHigh');
    const dailyLowEl = document.getElementById('gpsDailyLow');
    const weeklyHighEl = document.getElementById('gpsWeeklyHigh');
    const weeklyLowEl = document.getElementById('gpsWeeklyLow');
    const supportPriceEl = document.getElementById('gpsSupportPrice');
    const resistancePriceEl = document.getElementById('gpsResistancePrice');

    if (currentPriceEl && state.price) {
        currentPriceEl.textContent = priceFormatter.format(state.price);
    }

    if (dailyHighEl && state.dailyGpHigh) {
        dailyHighEl.textContent = priceFormatter.format(state.dailyGpHigh);
    }

    if (dailyLowEl && state.dailyGpLow) {
        dailyLowEl.textContent = priceFormatter.format(state.dailyGpLow);
    }

    if (weeklyHighEl && state.weeklyGpHigh) {
        weeklyHighEl.textContent = priceFormatter.format(state.weeklyGpHigh);
    }

    if (weeklyLowEl && state.weeklyGpLow) {
        weeklyLowEl.textContent = priceFormatter.format(state.weeklyGpLow);
    }

    if (supportPriceEl && state.support) {
        supportPriceEl.textContent = priceFormatter.format(state.support);
    }

    if (resistancePriceEl && state.resistance) {
        resistancePriceEl.textContent = priceFormatter.format(state.resistance);
    }
}

function initGpsPopup() {
    const gpsPill = document.getElementById('gpsPill');
    const gpsPopup = document.getElementById('gpsPopup');

    if (gpsPill && gpsPopup) {
        // Move popup to body to avoid stacking context issues
        const popupClone = gpsPopup.cloneNode(true);
        popupClone.id = 'gpsPopupFloating';
        popupClone.style.display = 'none';
        document.body.appendChild(popupClone);

        gpsPill.addEventListener('click', (e) => {
            e.stopPropagation();

            const isActive = popupClone.classList.contains('active');

            if (isActive) {
                // Close popup
                popupClone.classList.remove('active');
                popupClone.style.display = 'none';
            } else {
                // Calculate position relative to viewport
                const rect = gpsPill.getBoundingClientRect();
                const popupWidth = 280;
                const popupHeight = 320;

                // Position popup below the pill, centered horizontally
                let left = rect.left + (rect.width / 2) - (popupWidth / 2);
                let top = rect.bottom + 10;

                // Adjust if popup would go off screen
                if (left < 10) left = 10;
                if (left + popupWidth > window.innerWidth - 10) {
                    left = window.innerWidth - popupWidth - 10;
                }

                // If popup would go off bottom, show above instead
                if (top + popupHeight > window.innerHeight - 10) {
                    top = rect.top - popupHeight - 10;
                }

                // Update values from original popup
                const originalValues = {
                    currentPrice: document.getElementById('gpsCurrentPrice')?.textContent || '--',
                    dailyHigh: document.getElementById('gpsDailyHigh')?.textContent || '--',
                    dailyLow: document.getElementById('gpsDailyLow')?.textContent || '--',
                    weeklyHigh: document.getElementById('gpsWeeklyHigh')?.textContent || '--',
                    weeklyLow: document.getElementById('gpsWeeklyLow')?.textContent || '--',
                    support: document.getElementById('gpsSupportPrice')?.textContent || '--',
                    resistance: document.getElementById('gpsResistancePrice')?.textContent || '--'
                };

                // Update cloned popup values
                const cloneCurrentPrice = popupClone.querySelector('#gpsCurrentPrice');
                const cloneDailyHigh = popupClone.querySelector('#gpsDailyHigh');
                const cloneDailyLow = popupClone.querySelector('#gpsDailyLow');
                const cloneWeeklyHigh = popupClone.querySelector('#gpsWeeklyHigh');
                const cloneWeeklyLow = popupClone.querySelector('#gpsWeeklyLow');
                const cloneSupport = popupClone.querySelector('#gpsSupportPrice');
                const cloneResistance = popupClone.querySelector('#gpsResistancePrice');

                if (cloneCurrentPrice) cloneCurrentPrice.textContent = originalValues.currentPrice;
                if (cloneDailyHigh) cloneDailyHigh.textContent = originalValues.dailyHigh;
                if (cloneDailyLow) cloneDailyLow.textContent = originalValues.dailyLow;
                if (cloneWeeklyHigh) cloneWeeklyHigh.textContent = originalValues.weeklyHigh;
                if (cloneWeeklyLow) cloneWeeklyLow.textContent = originalValues.weeklyLow;
                if (cloneSupport) cloneSupport.textContent = originalValues.support;
                if (cloneResistance) cloneResistance.textContent = originalValues.resistance;

                // Apply position and show
                popupClone.style.left = `${left}px`;
                popupClone.style.top = `${top}px`;
                popupClone.style.display = 'block';
                popupClone.classList.add('active');
            }
        });

        // Close popup when clicking outside
        document.addEventListener('click', (e) => {
            if (!gpsPill.contains(e.target) && !popupClone.contains(e.target)) {
                popupClone.classList.remove('active');
                popupClone.style.display = 'none';
            }
        });

        // Close on scroll
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            if (popupClone.classList.contains('active')) {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    popupClone.classList.remove('active');
                    popupClone.style.display = 'none';
                }, 100);
            }
        }, { passive: true });
    }
}

function getNextScanTime(now = new Date()) {
    const next = new Date(now);
    next.setSeconds(0, 0);
    const minutes = next.getMinutes();
    if (minutes < 30) {
        next.setMinutes(30);
    } else {
        next.setHours(next.getHours() + 1);
        next.setMinutes(0);
    }
    return next;
}

function startScanTimer() {
    if (!state.nextScanAt) {
        state.nextScanAt = getNextScanTime().getTime();
    }
    setInterval(() => {
        const now = new Date();
        if (now.getTime() >= state.nextScanAt) {
            runScanCheck();
            state.nextScanAt = getNextScanTime(now).getTime();
        }
        const remaining = Math.max(0, state.nextScanAt - now.getTime());
        const mins = String(Math.floor(remaining / 60000)).padStart(2, '0');
        const secs = String(Math.floor((remaining % 60000) / 1000)).padStart(2, '0');
        const timerEl = document.getElementById('nextScanTimer');
        if (timerEl) timerEl.textContent = `${mins}:${secs}`;
    }, 1000);
}

function runScanCheck() {
    // Placeholder for bot-style scan summary
    updateDistanceBadges();
    const lastScanEl = document.getElementById('lastScanAt');
    if (lastScanEl) {
        const now = new Date();
        lastScanEl.textContent = formatLocalTimestamp(now.toISOString());
    }
    const statusEl = document.getElementById('botStatus');
    if (statusEl) {
        statusEl.textContent = 'SCANNING';
        setTimeout(() => {
            statusEl.textContent = 'ACTIVE';
        }, 4000);
    }
}

async function fetchBotStatus() {
    try {
        const response = await fetch(`bounty_seeker_status.json?ts=${Date.now()}`);
        if (!response.ok) return;
        const data = await response.json();
        renderEngagement(data);
    } catch (error) {
        console.error('Failed to fetch bot status:', error);
    }
}

function renderEngagement(data) {
    const signalCountEl = document.getElementById('signalCount');
    const watchlistCountEl = document.getElementById('watchlistCount');
    if (signalCountEl) {
        const currentSignals = (data.signals && data.signals.length) ? data.signals : (data.last_signals || []);
        signalCountEl.textContent = currentSignals.length;
    }
    if (watchlistCountEl) watchlistCountEl.textContent = data.watchlist_size || '--';

    const sessionEl = document.getElementById('sessionStatus');
    if (sessionEl) sessionEl.textContent = getSessionStatus();
    updateLastSessionHighLow();

    const lastScanEl = document.getElementById('lastScanAt');
    if (lastScanEl && data.last_scan_time) {
        lastScanEl.textContent = formatLocalTimestamp(data.last_scan_time);
    }

    const spotlightEl = document.getElementById('spotlightTrade');
    const reasonsEl = document.getElementById('spotlightReasons');
    const topSignal = data.signals && data.signals.length ? data.signals[0] : null;

    if (topSignal) {
        const bias = topSignal.direction || 'LONG';
        spotlightEl.textContent = `${topSignal.symbol} • ${bias} • Score ${topSignal.confidence_score}/100 • Entry ${priceFormatter.format(topSignal.entry_price)}`;
        reasonsEl.innerHTML = (topSignal.reasons || []).slice(0, 3).map(r => `<li>${r}</li>`).join('');
    } else if (data.spotlight) {
        const spotPct = Number.parseFloat(data.spotlight.change_pct);
        const spotPctText = Number.isFinite(spotPct) ? spotPct.toFixed(2) : '0.00';
        spotlightEl.textContent = `${data.spotlight.symbol} • ${spotPctText}% • ${data.spotlight.reason || 'Standout'}`;
        reasonsEl.innerHTML = `
                    <li>Top mover outside top 10</li>
                    <li>Volume: ${data.spotlight.volume ? priceFormatter.format(data.spotlight.volume) : 'N/A'}</li>
                    <li>Monitoring for reversal setup</li>
                `;
    } else {
        spotlightEl.textContent = 'Waiting for next scan...';
        reasonsEl.innerHTML = `
                    <li>GPS zones + Piv X VWAPs</li>
                    <li>Volume spikes with VPSR</li>
                    <li>Divergence via Oath Keeper</li>
                `;
    }

    renderTrendingCoins(data.trending_coins || []);
    renderTopMovers(data.top_gainers || [], data.top_losers || []);

    const displaySignals = (data.signals && data.signals.length) ? data.signals : (data.last_signals || []);
    updateSignalsPanel(displaySignals);
    updateWatchlistPanel(data.watchlist_candidates || []);
}

function renderTrendingCoins(coins) {
    const list = document.getElementById('trendingCoins');
    if (!list) return;
    if (!coins.length) {
        list.innerHTML = '<li>Waiting for ticker data...</li>';
        return;
    }
    list.innerHTML = coins.slice(0, 5).map(c => {
        const pctVal = Number.parseFloat(c.change_pct);
        const pct = Number.isFinite(pctVal) ? pctVal.toFixed(2) : '0.00';
        const link = getTradingViewLink(c.symbol);
        const label = normalizeBaseSymbol(c.symbol);
        return `<li><a href="${link}" target="_blank" rel="noopener">${label}</a> <span style="float:right; color:${pctVal >= 0 ? 'var(--accent-green)' : 'var(--accent-purple)'}">${pct}%</span></li>`;
    }).join('');
}

function normalizeBaseSymbol(symbol) {
    if (!symbol) return '';
    return symbol.split('/')[0].split(':')[0];
}

function getTradingViewLink(symbol) {
    const base = normalizeBaseSymbol(symbol);
    if (!base) return 'https://www.tradingview.com/';
    return `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(base)}USDT`;
}

function renderTopMovers(gainers, losers) {
    const gainersEl = document.getElementById('topGainers');
    const losersEl = document.getElementById('topLosers');
    if (gainersEl) {
        if (!gainers.length) {
            gainersEl.innerHTML = '<li>Waiting for ticker data...</li>';
        } else {
            gainersEl.innerHTML = gainers.slice(0, 5).map(c => {
                const pctVal = Number.parseFloat(c.change_pct);
                const pct = Number.isFinite(pctVal) ? pctVal.toFixed(2) : '0.00';
                const link = getTradingViewLink(c.symbol);
                const label = normalizeBaseSymbol(c.symbol);
                return `<li><a href="${link}" target="_blank" rel="noopener">${label}</a> <span class="pos">${pct}%</span></li>`;
            }).join('');
        }
    }
    if (losersEl) {
        if (!losers.length) {
            losersEl.innerHTML = '<li>Waiting for ticker data...</li>';
        } else {
            losersEl.innerHTML = losers.slice(0, 5).map(c => {
                const pctVal = Number.parseFloat(c.change_pct);
                const pct = Number.isFinite(pctVal) ? pctVal.toFixed(2) : '0.00';
                const link = getTradingViewLink(c.symbol);
                const label = normalizeBaseSymbol(c.symbol);
                return `<li><a href="${link}" target="_blank" rel="noopener">${label}</a> <span class="neg">${pct}%</span></li>`;
            }).join('');
        }
    }
}

function getSessionStatus() {
    const now = new Date();
    const hour = now.getUTCHours();
    if (hour >= 7 && hour < 10) return 'London';
    if (hour >= 13 && hour < 16) return 'New York';
    if (hour >= 0 && hour < 7) return 'Asia';
    return 'Off-Session';
}

function getLastClosedSessionWindow(now = new Date()) {
    const year = now.getUTCFullYear();
    const month = now.getUTCMonth();
    const day = now.getUTCDate();
    const hour = now.getUTCHours();

    // Helper to build UTC date
    const utc = (d, h) => new Date(Date.UTC(year, month, d, h, 0, 0));

    // Sessions: Asia (00:00-08:00), London (08:00-13:00), NY (13:00-21:00)
    if (hour >= 8 && hour < 13) {
        // London active -> last closed Asia
        return { name: 'Asia', start: utc(day, 0), end: utc(day, 8) };
    }
    if (hour >= 13 && hour < 21) {
        // New York active -> last closed London
        return { name: 'London', start: utc(day, 8), end: utc(day, 13) };
    }
    if (hour >= 21) {
        // After NY close -> last closed New York
        return { name: 'New York', start: utc(day, 13), end: utc(day, 21) };
    }
    // Asia active (00-08) -> last closed New York (previous day)
    const prevDay = new Date(Date.UTC(year, month, day - 1));
    return { name: 'New York', start: new Date(Date.UTC(prevDay.getUTCFullYear(), prevDay.getUTCMonth(), prevDay.getUTCDate(), 13)), end: new Date(Date.UTC(prevDay.getUTCFullYear(), prevDay.getUTCMonth(), prevDay.getUTCDate(), 21)) };
}

async function updateLastSessionHighLow() {
    const highEl = document.getElementById('sessionHigh');
    const lowEl = document.getElementById('sessionLow');
    const sessionLabelEl = document.getElementById('sessionLabel');
    if (!highEl || !lowEl) return;

    try {
        const windowInfo = getLastClosedSessionWindow();
        const startTs = windowInfo.start.getTime();
        const endTs = windowInfo.end.getTime();

        // Fetch 1H candles from OKX for the session window
        const instId = state.instId || 'BTC-USDT-SWAP';
        const url = `https://www.okx.com/api/v5/market/candles?instId=${instId}&bar=1H&after=${endTs}&before=${startTs - 1}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch session candles');
        const json = await res.json();
        const candles = json.data || [];

        // Filter candles within session window
        const sessionCandles = candles.filter(c => {
            const ts = Number(c[0]);
            return ts >= startTs && ts < endTs;
        });

        if (!sessionCandles.length) {
            // Fallback: fetch recent candles
            const fallbackUrl = `https://www.okx.com/api/v5/market/candles?instId=${instId}&bar=1H&limit=24`;
            const fallbackRes = await fetch(fallbackUrl);
            const fallbackJson = await fallbackRes.json();
            const allCandles = fallbackJson.data || [];

            const filtered = allCandles.filter(c => {
                const ts = Number(c[0]);
                return ts >= startTs && ts < endTs;
            });

            if (filtered.length) {
                let high = -Infinity;
                let low = Infinity;
                filtered.forEach(c => {
                    const h = Number(c[2]);
                    const l = Number(c[3]);
                    if (h > high) high = h;
                    if (l < low) low = l;
                });
                highEl.textContent = priceFormatter.format(high);
                lowEl.textContent = priceFormatter.format(low);
                if (sessionLabelEl) sessionLabelEl.textContent = windowInfo.name;
                const sessionLabel2El = document.getElementById('sessionLabel2');
                if (sessionLabel2El) sessionLabel2El.textContent = windowInfo.name;
                return;
            }

            highEl.textContent = '--';
            lowEl.textContent = '--';
            return;
        }

        let high = -Infinity;
        let low = Infinity;
        sessionCandles.forEach(c => {
            const h = Number(c[2]);
            const l = Number(c[3]);
            if (h > high) high = h;
            if (l < low) low = l;
        });

        highEl.textContent = priceFormatter.format(high);
        lowEl.textContent = priceFormatter.format(low);
        if (sessionLabelEl) sessionLabelEl.textContent = windowInfo.name;
        const sessionLabel2El = document.getElementById('sessionLabel2');
        if (sessionLabel2El) sessionLabel2El.textContent = windowInfo.name;
    } catch (e) {
        console.error('Failed to fetch session high/low:', e);
        highEl.textContent = '--';
        lowEl.textContent = '--';
    }
}

function formatLocalTimestamp(isoString) {
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) return '--';
    return date.toLocaleString(undefined, {
        dateStyle: 'short',
        timeStyle: 'short'
    });
}

function loadSignalHistory() {
    try {
        const stored = localStorage.getItem('signal_history');
        signalHistory = stored ? JSON.parse(stored) : [];
    } catch (e) {
        signalHistory = [];
    }
}

function saveSignalHistory() {
    try {
        localStorage.setItem('signal_history', JSON.stringify(signalHistory.slice(0, 100)));
    } catch (e) {
        // ignore storage errors
    }
}

function normalizeSignal(signal) {
    return {
        id: `${signal.symbol}-${signal.direction}-${signal.entry_price}-${signal.timestamp}`,
        symbol: signal.symbol,
        direction: signal.direction || 'LONG',
        entry_price: signal.entry_price,
        stop_loss: signal.stop_loss,
        take_profit: signal.take_profit,
        confidence_score: signal.confidence_score,
        timestamp: signal.timestamp,
        tradingview_link: signal.tradingview_link
    };
}

function getSignalStatus(signal) {
    if (!state.price) return 'ACTIVE';
    const price = state.price;
    const dir = signal.direction;
    if (dir === 'LONG') {
        if (price >= signal.take_profit) return 'HIT_TP';
        if (price <= signal.stop_loss) return 'HIT_SL';
        return 'ACTIVE';
    }
    if (dir === 'SHORT') {
        if (price <= signal.take_profit) return 'HIT_TP';
        if (price >= signal.stop_loss) return 'HIT_SL';
        return 'ACTIVE';
    }
    return 'ACTIVE';
}

function updateSignalsPanel(currentSignals) {
    const signalList = document.getElementById('signalList');
    const historyList = document.getElementById('signalHistory');
    if (!signalList || !historyList) return;

    const normalizedCurrent = currentSignals.map(normalizeSignal);
    const currentIds = new Set(normalizedCurrent.map(s => s.id));

    normalizedCurrent.forEach(signal => {
        if (!signalHistory.find(s => s.id === signal.id)) {
            signalHistory.unshift({ ...signal, status: 'ACTIVE' });
        }
    });

    signalHistory = signalHistory.map(signal => {
        const status = getSignalStatus(signal);
        return { ...signal, status };
    });

    saveSignalHistory();

    signalList.innerHTML = normalizedCurrent.length
        ? normalizedCurrent.map(renderSignalItem).join('')
        : '<div class="signal-item">No live signals yet.</div>';

    historyList.innerHTML = signalHistory.length
        ? signalHistory.map(renderSignalItem).join('')
        : '<div class="signal-item">No past signals yet.</div>';
}

function renderSignalItem(signal) {
    const status = signal.status || 'ACTIVE';
    const dirClass = signal.direction === 'SHORT' ? 'short' : 'long';
    const statusClass = status === 'HIT_TP' ? 'tp' : status === 'HIT_SL' ? 'sl' : 'active';
    const statusLabel = status === 'HIT_TP' ? 'VALID' : status === 'HIT_SL' ? 'INVALID' : 'ACTIVE';
    const timeLabel = formatLocalTimestamp(signal.timestamp);
    const link = signal.tradingview_link || getTradingViewLink(signal.symbol);

    return `
                <div class="signal-item">
                    <div class="signal-meta">
                        <div>${signal.symbol}</div>
                        <div>
                            <span class="signal-badge ${dirClass}">${signal.direction}</span>
                            <span class="signal-badge ${statusClass}">${statusLabel}</span>
                </div>
                </div>
                    <div class="signal-details">
                        Entry: ${formatSignalPrice(signal.entry_price)} | TP: ${formatSignalPrice(signal.take_profit)} | SL: ${formatSignalPrice(signal.stop_loss)}
                        <br>${timeLabel} • <a href="${link}" target="_blank" rel="noopener">Chart</a>
                    </div>
                </div>
            `;
}

function updateWatchlistPanel(candidates) {
    const listEl = document.getElementById('watchlistList');
    if (!listEl) return;

    // If no candidates from bot, scan for our own
    if (!candidates.length) {
        scanWatchlistCandidates();
        return;
    }

    renderWatchlistItems(candidates);
}

function renderWatchlistItems(candidates) {
    const listEl = document.getElementById('watchlistList');
    const countEl = document.getElementById('watchlistCount');
    if (!listEl) return;

    if (!candidates.length) {
        listEl.innerHTML = '<div class="signal-item">No coins near key levels right now.</div>';
        if (countEl) countEl.textContent = '0';
        return;
    }

    if (countEl) countEl.textContent = candidates.length;

    listEl.innerHTML = candidates.map(item => {
        const symbol = item.symbol;
        const label = normalizeBaseSymbol(symbol);
        const link = getTradingViewLink(symbol);
        const reasons = (item.reasons || []).join(' • ');
        const bias = item.bias || '';
        const biasClass = bias === 'LONG' ? 'value-up' : bias === 'SHORT' ? 'value-down' : '';
        return `
                    <div class="signal-item">
                        <div class="signal-meta">
                            <div><strong>${label}</strong> ${bias ? `<span class="${biasClass}" style="font-size:0.8em;">${bias}</span>` : ''}</div>
                            <div><a href="${link}" target="_blank" rel="noopener">Chart</a></div>
                        </div>
                        <div class="signal-details">
                            Price: ${priceFormatter.format(item.price)}<br>
                            <span style="color:var(--text-secondary);font-size:0.85em;">${reasons}</span>
                        </div>
                    </div>
                `;
    }).join('');
}

async function scanWatchlistCandidates() {
    const listEl = document.getElementById('watchlistList');
    if (!listEl) return;

    listEl.innerHTML = '<div class="signal-item">Scanning for setups...</div>';

    try {
        // Fetch top coins by volume
        const tickersRes = await fetch('https://www.okx.com/api/v5/market/tickers?instType=SWAP');
        if (!tickersRes.ok) throw new Error('Failed to fetch tickers');
        const tickersJson = await tickersRes.json();
        const tickers = tickersJson.data || [];

        const stableBases = new Set(['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD']);
        const topCoins = tickers
            .filter(t => t.instId && t.instId.endsWith('-USDT-SWAP'))
            .filter(t => !stableBases.has(t.instId.split('-')[0]))
            .sort((a, b) => Number(b.volCcy24h || 0) - Number(a.volCcy24h || 0))
            .slice(0, 15);

        const candidates = [];

        for (const ticker of topCoins) {
            const instId = ticker.instId;
            const symbol = instId.split('-')[0];
            const price = Number(ticker.last);
            if (!price) continue;

            // Fetch daily candle for GP calculation
            try {
                const candleRes = await fetch(`https://www.okx.com/api/v5/market/candles?instId=${instId}&bar=1D&limit=1`);
                if (!candleRes.ok) continue;
                const candleJson = await candleRes.json();
                const candle = candleJson.data && candleJson.data[0];
                if (!candle) continue;

                const high = Number(candle[2]);
                const low = Number(candle[3]);
                const gpHigh = high - (high - low) * 0.618;
                const gpLow = high - (high - low) * 0.65;

                // Check proximity to GP zones
                const distToGpLow = ((price - gpLow) / price) * 100;
                const distToGpHigh = ((gpHigh - price) / price) * 100;
                const distToSupport = ((price - low) / price) * 100;
                const distToResistance = ((high - price) / price) * 100;

                const reasons = [];
                let bias = '';
                let score = 0;

                // Near daily GP zone (within 1.5%)
                if (price >= gpLow && price <= gpHigh) {
                    reasons.push('Inside Daily GP Zone');
                    score += 30;
                } else if (Math.abs(distToGpLow) <= 1.5) {
                    reasons.push(`${Math.abs(distToGpLow).toFixed(1)}% from GP Low`);
                    bias = 'LONG';
                    score += 25;
                } else if (Math.abs(distToGpHigh) <= 1.5) {
                    reasons.push(`${Math.abs(distToGpHigh).toFixed(1)}% from GP High`);
                    bias = 'SHORT';
                    score += 25;
                }

                // Near daily support/resistance (within 2%)
                if (distToSupport <= 2.0 && distToSupport > 0) {
                    reasons.push(`${distToSupport.toFixed(1)}% from Daily Support`);
                    bias = bias || 'LONG';
                    score += 20;
                }

                if (distToResistance <= 2.0 && distToResistance > 0) {
                    reasons.push(`${distToResistance.toFixed(1)}% from Daily Resistance`);
                    bias = bias || 'SHORT';
                    score += 20;
                }

                if (reasons.length > 0) {
                    candidates.push({
                        symbol,
                        price,
                        reasons,
                        bias,
                        score,
                        gpHigh,
                        gpLow
                    });
                }
            } catch (e) {
                continue;
            }
        }

        // Sort by score and take top 2 for watchlist (User requested 2 per hour)
        candidates.sort((a, b) => b.score - a.score);
        renderWatchlistItems(candidates.slice(0, 2));

        // ### FIXED: Generate live signals for top 2 candidates (User requested 2 per hour) ###
        const topSignals = candidates.slice(0, 2).map(c => {
            const isLong = c.bias === 'LONG';
            const entry = c.price;
            const tp = isLong
                ? (c.gpHigh > entry ? c.gpHigh : entry * 1.04)
                : (c.gpLow < entry ? c.gpLow : entry * 0.96);
            const sl = isLong
                ? (c.gpLow < entry ? c.gpLow * 0.99 : entry * 0.99)
                : (c.gpHigh > entry ? c.gpHigh * 1.01 : entry * 1.01);

            return {
                id: 'sig_' + c.symbol + '_' + Date.now(),
                symbol: c.symbol,
                timestamp: new Date().toISOString(),
                direction: c.bias || 'NEUTRAL',
                entry_price: entry,
                take_profit: tp,
                stop_loss: sl,
                confidence_score: c.score,
                reasons: c.reasons,
                status: 'ACTIVE'
            };
        });

        if (topSignals.length > 0) {
            // Discord Notification for Signals (Purple Card)
            // Deduplication Logic: Check if we sent this exact symbol in the last 60 minutes
            const currentSymbol = topSignals[0].symbol;
            const currentTime = Date.now();

            // Check if we sent this symbol recently (last 60 mins)
            const lastSentTime = signalSentTimes.get(currentSymbol) || 0;
            const isTimeExpired = (currentTime - lastSentTime) > 60 * 60 * 1000;

            if (isTimeExpired) {
                signalSentTimes.set(currentSymbol, currentTime);

                updateSignalsPanel(topSignals);
                // Update header counts
                const signalCountEl = document.getElementById('signalCount');
                if (signalCountEl) signalCountEl.textContent = topSignals.length;

                sendToDiscord({
                    username: "Bounty Seeker Bot",
                    avatar_url: "https://i.imgur.com/4M34hi2.png",
                    embeds: [{
                        title: `🎯 ${topSignals.length} New High-Confidence Signal Detected`,
                        color: 10181046, // Purple
                        fields: topSignals.map(s => ({
                            name: `${s.symbol} ${s.direction} (Score: ${s.confidence_score})`,
                            value: `Entry: ${formatSignalPrice(s.entry_price)}\nTP: ${formatSignalPrice(s.take_profit)}\nSL: ${formatSignalPrice(s.stop_loss)}\nReasons: ${s.reasons.join(', ')}`
                        })),
                        footer: { text: "Snipers R Us • Live Scanner" },
                        timestamp: new Date().toISOString()
                    }]
                });
            } else {
                console.log(`[Signal Skipped] ${currentSymbol} sent recently (${new Date(lastDiscordSignalTime).toLocaleTimeString()})`);
            }
        }

        // Discord Notification for Watchlist (Orange Card)
        // Deduplication: Only send if the top 5 candidates have changed
        if (candidates.length > 0) {
            const currentWatchlistSignature = candidates.slice(0, 5).map(c => c.symbol + c.bias).join('|');

            if (currentWatchlistSignature !== lastWatchlistHash) {
                lastWatchlistHash = currentWatchlistSignature;
                sendToDiscord({
                    username: "Bounty Seeker Bot",
                    avatar_url: "https://i.imgur.com/4M34hi2.png",
                    embeds: [{
                        title: `👀 Watchlist Update: ${candidates.length} Sets in Focus`,
                        color: 16753920, // Orange
                        description: candidates.slice(0, 5).map(c => `**${c.symbol}** (${c.bias || 'Neutral'}) - ${c.reasons[0]}`).join('\n'),
                        footer: { text: "Snipers R Us • Watchlist" },
                        timestamp: new Date().toISOString()
                    }]
                });
            } else {
                console.log('[Watchlist Skipped] No change in top 5 candidates');
            }
        }

    } catch (error) {
        console.error('Failed to scan watchlist candidates:', error);
        listEl.innerHTML = '<div class="signal-item">Scan failed. Retrying...</div>';
    }
}

function updateConnectionStatus(connected) {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('connectionStatus');

    if (connected) {
        if (dot) {
            dot.className = 'status-dot';
            dot.style.background = 'var(--neon-green)';
            dot.style.boxShadow = '0 0 10px var(--neon-green)';
        }
        if (text) {
            text.textContent = 'Connected to OKX';
            text.style.color = 'var(--neon-green)';
        }
        if (restPollTimer) {
            clearInterval(restPollTimer);
            restPollTimer = null;
        }
    } else {
        if (dot) {
            dot.className = 'status-dot disconnected';
            dot.style.background = '#ff3b30';
            dot.style.boxShadow = '0 0 10px #ff3b30';
        }
        if (text) {
            text.textContent = 'Disconnected - Reconnecting...';
            text.style.color = '#ff3b30';
        }
        if (!restPollTimer) {
            restPollTimer = setInterval(fetchOkxTicker, 15000);
        }
    }
}

async function fetchOkxTicker() {
    console.log('[DEBUG] fetchOkxTicker called', state.instId);
    try {
        const response = await fetch(`${OKX_BASE_URL}/ticker?instId=${state.instId}`, {
            cache: 'no-cache',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            console.error(`OKX ticker request failed: ${response.status} ${response.statusText}`);
            // Try fallback to Binance
            await fetchBinanceTicker();
            return;
        }

        const result = await response.json();
        console.log('[DEBUG] OKX ticker response:', result);

        const ticker = result.data && result.data[0];
        if (!ticker) {
            console.error('OKX ticker data not available');
            // Try fallback to Binance
            await fetchBinanceTicker();
            return;
        }

        const price = parseFloat(ticker.last);
        const open24h = parseFloat(ticker.open24h);
        const volume24h = parseFloat(ticker.volCcy24h);

        console.log('[DEBUG] Ticker price:', price, '24h change:', open24h);

        if (!Number.isNaN(price)) {
            state.volume24h = Number.isNaN(volume24h) ? state.volume24h : volume24h;
            if (!Number.isNaN(open24h) && open24h > 0) {
                state.pct24h = ((price - open24h) / open24h) * 100;
            }
            updateMarket(price, 0);
            return price;
        }
    } catch (error) {
        console.error('Failed to fetch OKX ticker:', error);
        // Try fallback to Binance
        await fetchBinanceTicker();
    }
}

// Fallback to Binance API if OKX fails
async function fetchBinanceTicker() {
    console.log('[DEBUG] Trying Binance ticker as fallback');
    try {
        const binanceSymbol = state.symbol.toLowerCase() + 'usdt';
        const response = await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbol=${binanceSymbol.toUpperCase()}`, {
            cache: 'no-cache'
        });

        if (!response.ok) {
            console.error('Binance ticker request failed');
            return;
        }

        const ticker = await response.json();
        const price = parseFloat(ticker.lastPrice);
        const open24h = parseFloat(ticker.openPrice);

        if (!Number.isNaN(price)) {
            console.log('[DEBUG] Binance price:', price);
            if (!Number.isNaN(open24h) && open24h > 0) {
                state.pct24h = ((price - open24h) / open24h) * 100;
            }
            updateMarket(price, 0);
            return price;
        }
    } catch (error) {
        console.error('Failed to fetch Binance ticker:', error);
    }
}

async function fetchOkxDailyCandle() {
    try {
        const response = await fetch(`${OKX_BASE_URL}/candles?instId=${state.instId}&bar=1D&limit=1`);
        const result = await response.json();
        const candle = result.data && result.data[0];
        if (!candle) return;

        const high = parseFloat(candle[2]);
        const low = parseFloat(candle[3]);
        if (Number.isNaN(high) || Number.isNaN(low)) return;

        state.dailyHigh = high;
        state.dailyLow = low;
        state.dailyGpHigh = high - (high - low) * 0.618;
        state.dailyGpLow = high - (high - low) * 0.65;
    } catch (error) {
        console.error('Failed to fetch OKX daily candle:', error);
    }
}

async function fetchOkxWeeklyCandle() {
    try {
        const instId = state.instId;
        const url = `${OKX_BASE_URL}/candles?instId=${instId}&bar=1W&limit=1`;
        const res = await fetch(url);
        if (!res.ok) return;
        const json = await res.json();
        if (!json.data || !json.data.length) return;

        const candle = json.data[0];
        const high = parseFloat(candle[2]);
        const low = parseFloat(candle[3]);
        if (Number.isNaN(high) || Number.isNaN(low)) return;

        state.weeklyGpHigh = high - (high - low) * 0.618;
        state.weeklyGpLow = high - (high - low) * 0.65;
    } catch (error) {
        console.error('Failed to fetch OKX weekly candle:', error);
    }
}

function startStaleCheck() {
    if (staleCheckTimer) return;
    staleCheckTimer = setInterval(() => {
        if (!state.lastUpdate) {
            console.log('[DEBUG] No price updates yet, fetching via REST API');
            fetchOkxTicker();
            return;
        }
        const ageMs = Date.now() - state.lastUpdate;
        if (ageMs > 8000) {
            console.log(`[DEBUG] Price data stale (${ageMs}ms), fetching via REST API`);
            fetchOkxTicker();
        }
    }, 5000);
}

function setPair(symbol) {
    if (symbol === 'SOL') {
        state.symbol = 'SOL';
        state.instId = 'SOL-USDT-SWAP';
        state.tvSymbol = 'OKX:SOLUSDT.P';
    } else if (symbol === 'ETH') {
        state.symbol = 'ETH';
        state.instId = 'ETH-USDT-SWAP';
        state.tvSymbol = 'OKX:ETHUSDT.P';
    } else if (symbol === 'XRP') {
        state.symbol = 'XRP';
        state.instId = 'XRP-USDT-SWAP';
        state.tvSymbol = 'OKX:XRPUSDT.P';
    } else {
        state.symbol = 'BTC';
        state.instId = 'BTC-USDT-SWAP';
        state.tvSymbol = 'OKX:BTCUSDT.P';
    }

    state.prices = [];
    state.volume = [];
    state.lastPrice = null;
    state.support = null;
    state.resistance = null;
    state.dailyHigh = null;
    state.dailyLow = null;
    state.dailyGpHigh = null;
    state.dailyGpLow = null;
    state.weeklyGpHigh = null;
    state.weeklyGpLow = null;
    state.lastUpdate = null;

    fetchOkxTicker();
    fetchOkxDailyCandle();
    fetchOkxWeeklyCandle();
    connectOKX();
    loadTradingViewWidget('tvEmbed');
    loadTradingViewWidget('paperTvEmbed');
    updatePairUI(symbol);

    // Force immediate price display update to "Loading..." or clear old data
    const priceEl = document.getElementById('btcPrice');
    if (priceEl) {
        priceEl.style.opacity = '0.5';
    }
}

function updatePairUI(symbol) {
    const pills = document.querySelectorAll('.pair-pill');
    pills.forEach(pill => {
        const isActive = pill.dataset.symbol === symbol;
        pill.classList.toggle('active', isActive);
    });
}

// ============================================
// THEME TOGGLE
// ============================================
// Track clicked buttons to stop glow animation
document.addEventListener('DOMContentLoaded', function () {
    const btnJoin = document.querySelector('.btn-join');
    const btnLarge = document.querySelector('.btn-large');
    const themeToggle = document.querySelector('.theme-toggle');

    if (btnJoin) {
        btnJoin.addEventListener('click', function () {
            if (!this.classList.contains('clicked')) {
                this.classList.add('clicked');
            }
        });
    }

    if (btnLarge) {
        btnLarge.addEventListener('click', function () {
            if (!this.classList.contains('clicked')) {
                this.classList.add('clicked');
            }
        });
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            if (!this.classList.contains('clicked')) {
                this.classList.add('clicked');
            }
        });
    }
});

function toggleTheme() {
    const body = document.body;
    const icon = document.getElementById('themeIcon');

    if (state.theme === 'dark') {
        body.setAttribute('data-theme', 'light');
        state.theme = 'light';
        icon.textContent = '☀️';
    } else {
        body.setAttribute('data-theme', 'dark');
        state.theme = 'dark';
        icon.textContent = '🌙';
    }

    localStorage.setItem('srus_theme', state.theme);

    // Reload TradingView widget to match theme
    // Reload TradingView widget to match theme
    loadTradingViewWidget('tvEmbed');
    loadTradingViewWidget('paperTvEmbed');
}

// ============================================
// INITIALIZATION
// ============================================
function init() {
    console.log('[DEBUG] init() started');
    console.log('[DEBUG] State:', state);
    console.log('[DEBUG] DOM ready?', document.readyState);

    // Load saved theme
    const savedTheme = localStorage.getItem('srus_theme');
    if (savedTheme) {
        state.theme = savedTheme;
        document.body.setAttribute('data-theme', savedTheme);
        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.textContent = savedTheme === 'light' ? '☀️' : '🌙';
        }
    }

    // Load initial price from REST
    fetchOkxTicker();
    fetchOkxDailyCandle();
    fetchOkxWeeklyCandle();

    // Initialize GPS popup
    initGpsPopup();

    setInterval(fetchOkxDailyCandle, 30 * 60 * 1000);
    setInterval(fetchOkxWeeklyCandle, 60 * 60 * 1000);

    // Connect to OKX
    connectOKX();

    // Safety fallback if WS stalls
    startStaleCheck();

    // Scanner timer
    startScanTimer();

    // TradingView embed
    loadTradingViewWidget('tvEmbed');
    loadTradingViewWidget('paperTvEmbed');

    // Pair switch buttons
    const pairSwitch = document.getElementById('pairSwitch');
    if (pairSwitch) {
        pairSwitch.addEventListener('click', (e) => {
            const btn = e.target.closest('.pair-pill');
            if (!btn) return;
            const symbol = btn.dataset.symbol;
            if (symbol) setPair(symbol);
        });
    }
    updatePairUI(state.symbol);

    // User Profile
    const profileBtn = document.getElementById('userProfileBtn');
    if (profileBtn) {
        profileBtn.addEventListener('click', setUsername);
        updateProfileUI();
    }

    // Engagement panels
    renderEngagement({ signals: [], watchlist_size: '--' });
    fetchBotStatus();
    setInterval(fetchBotStatus, 30000);

    // Free trial modal (15s delay, only once)
    if (!localStorage.getItem('trial_shown')) {
        setTimeout(() => {
            const overlay = document.getElementById('trialOverlay');
            if (overlay) overlay.style.display = 'flex';
            localStorage.setItem('trial_shown', 'true');
        }, 15000);
    }

    // Initial watchlist scan (after 5s to let prices load)
    setTimeout(scanWatchlistCandidates, 5000);
    // Rescan every 1 hour (as requested)
    setInterval(scanWatchlistCandidates, 60 * 60 * 1000);
}

function closeTrialModal() {
    const overlay = document.getElementById('trialOverlay');
    if (overlay) overlay.style.display = 'none';
}

function loadTradingViewWidget(targetId = 'tvEmbed') {
    const container = document.getElementById(targetId);
    if (!container) return;
    container.innerHTML = `
                <div class="tradingview-widget-container" style="height:100%;width:100%">
                    <div class="tradingview-widget-container__widget" style="height:100%;width:100%"></div>
    </div>
            `;

    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.async = true;
    script.text = JSON.stringify({
        autosize: true,
        symbol: state.tvSymbol,
        interval: '15',
        timezone: 'local',
        theme: state.theme === 'light' ? 'light' : 'dark',
        style: '1',
        locale: 'en',
        hide_top_toolbar: false,
        hide_legend: false,
        hide_side_toolbar: false,
        allow_symbol_change: false,
        details: false,
        calendar: false,
        backgroundColor: state.theme === 'light' ? '#ffffff' : '#0f1115', // Match card background
        studies: [], // Users requested no indicators on the chart
        overrides: {
            "paneProperties.background": state.theme === 'light' ? "#ffffff" : "#0f1115",
            "paneProperties.vertGridProperties.color": state.theme === 'light' ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)",
            "paneProperties.horzGridProperties.color": state.theme === 'light' ? "rgba(0,0,0,0.05)" : "rgba(255,255,255,0.05)",
            "mainSeriesProperties.candleStyle.upColor": "#22c55e",
            "mainSeriesProperties.candleStyle.downColor": "#a855f7",
            "mainSeriesProperties.candleStyle.borderUpColor": "#22c55e",
            "mainSeriesProperties.candleStyle.borderDownColor": "#a855f7",
            "mainSeriesProperties.candleStyle.wickUpColor": "#22c55e",
            "mainSeriesProperties.candleStyle.wickDownColor": "#a855f7"
        }
    });

    const widgetContainer = container.querySelector('.tradingview-widget-container');
    if (widgetContainer) {
        widgetContainer.appendChild(script);
    }
}

function formatCompactNumber(number) {
    return Intl.NumberFormat('en-US', {
        notation: "compact",
        maximumFractionDigits: 1
    }).format(number);
}

function initSignalPanel() {
    const toggle = document.getElementById('signalToggle');
    const closeBtn = document.getElementById('signalClose');
    const clearBtn = document.getElementById('signalClear');
    const panel = document.getElementById('signalPanel');
    const watchlistToggle = document.getElementById('watchlistToggle');
    const watchlistClose = document.getElementById('watchlistClose');
    const watchlistPanel = document.getElementById('watchlistPanel');

    if (toggle && panel) {
        toggle.addEventListener('click', () => {
            panel.classList.toggle('active');
            panel.setAttribute('aria-hidden', panel.classList.contains('active') ? 'false' : 'true');
        });
    }
    if (closeBtn && panel) {
        closeBtn.addEventListener('click', () => {
            panel.classList.remove('active');
            panel.setAttribute('aria-hidden', 'true');
        });
    }
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            signalHistory = [];
            saveSignalHistory();
            updateSignalsPanel([]);
        });
    }

    if (watchlistToggle && watchlistPanel) {
        watchlistToggle.addEventListener('click', () => {
            watchlistPanel.classList.toggle('active');
            watchlistPanel.setAttribute('aria-hidden', watchlistPanel.classList.contains('active') ? 'false' : 'true');
        });
    }
    if (watchlistClose && watchlistPanel) {
        watchlistClose.addEventListener('click', () => {
            watchlistPanel.classList.remove('active');
            watchlistPanel.setAttribute('aria-hidden', 'true');
        });
    }
}

// ============================================
// NEWS FEED FUNCTIONALITY
// ============================================
const newsData = [
    {
        impact: 'critical',
        category: 'regulation',
        coins: ['BTC', 'Bitcoin'],
        title: 'SEC Announces Major Bitcoin Regulation - Market Plunges 15%',
        excerpt: 'The Securities and Exchange Commission has announced sweeping new regulations for Bitcoin trading, causing immediate market panic and a 15% price drop across major exchanges.',
        source: 'CoinTelegraph',
        timeAgo: '2h ago',
        link: 'https://cointelegraph.com',
        trend: '📉'
    },
    {
        impact: 'high',
        category: 'defi',
        coins: ['ETH', 'Ethereum', 'UNI'],
        title: 'Vitalik Buterin Announces Ethereum 2.0 Upgrade Timeline - DeFi Surges',
        excerpt: 'Ethereum founder Vitalik Buterin revealed the final timeline for the Ethereum 2.0 merge, sparking a massive rally in DeFi tokens and ETH price surging 12% in hours.',
        source: 'CryptoPanic',
        timeAgo: '5h ago',
        link: 'https://cointelegraph.com',
        trend: '📈'
    },
    {
        impact: 'medium',
        category: 'trading',
        coins: ['BTC', 'Bitcoin'],
        title: 'Bitcoin Flashes Buy Signals as $90K Becomes Key Support Level',
        excerpt: 'Technical analysts are pointing to strong buy signals as Bitcoin consolidates above the critical $90,000 support level, with potential for a breakout rally.',
        source: 'CoinTelegraph',
        timeAgo: '8h ago',
        link: 'https://cointelegraph.com',
        trend: '📈'
    },
    {
        impact: 'high',
        category: 'regulation',
        coins: ['BTC', 'Bitcoin'],
        title: 'Trump Announces Bitcoin Policy Stance - Market Reacts Instantly',
        excerpt: 'Former President Trump made statements about Bitcoin regulation during a campaign event, causing immediate volatility as traders react to potential policy changes.',
        source: 'Twitter / News',
        timeAgo: '3h ago',
        link: 'https://twitter.com',
        trend: '📉'
    },
    {
        impact: 'medium',
        category: 'nft',
        coins: ['ETH'],
        title: 'South Korea Weighs Ending One-Bank Rule for Crypto Exchanges',
        excerpt: 'Regulatory authorities in South Korea are considering changes to the banking requirements for cryptocurrency exchanges, potentially opening up more competition.',
        source: 'CoinDesk',
        timeAgo: '12h ago',
        link: 'https://coindesk.com',
        trend: '➡️'
    },
    {
        impact: 'medium',
        category: 'tech',
        coins: ['ETH', 'Ethereum'],
        title: 'Ethereum Layer 2 Solutions See Record Adoption',
        excerpt: 'Arbitrum and Optimism report record transaction volumes as users migrate to cheaper Layer 2 solutions for DeFi operations.',
        source: 'The Block',
        timeAgo: '6h ago',
        link: 'https://theblock.co',
        trend: '📈'
    },
    {
        impact: 'high',
        category: 'trading',
        coins: ['BTC', 'Bitcoin'],
        title: 'Major Exchange Lists New Bitcoin ETF Products',
        excerpt: 'A leading exchange announces the listing of multiple Bitcoin ETF products, providing institutional investors with new ways to gain exposure.',
        source: 'Bloomberg Crypto',
        timeAgo: '4h ago',
        link: 'https://bloomberg.com',
        trend: '📈'
    },
    {
        impact: 'medium',
        category: 'defi',
        coins: ['ETH', 'UNI'],
        title: 'Uniswap V4 Launch Date Confirmed',
        excerpt: 'The Uniswap team confirms the launch date for V4, introducing new features that could revolutionize decentralized exchange trading.',
        source: 'DeFi Pulse',
        timeAgo: '10h ago',
        link: 'https://defipulse.com',
        trend: '📈'
    }
];

let currentNewsCategory = 'all';
let currentMarket = 'all';
let yahooNewsData = [];

// Yahoo Finance RSS Feed URLs
const yahooFeeds = {
    stocks: 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL,MSFT,GOOGL,AMZN,TSLA&region=US&lang=en-US',
    forex: 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=EURUSD=X,GBPUSD=X,USDJPY=X&region=US&lang=en-US',
    commodities: 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F,CL=F,SI=F&region=US&lang=en-US',
    crypto: 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=BTC-USD,ETH-USD&region=US&lang=en-US',
    economy: 'https://feeds.finance.yahoo.com/rss/2.0/headline?category=economy&region=US&lang=en-US'
};

// Parse RSS XML
function parseRSS(xmlText) {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
    const items = xmlDoc.querySelectorAll('item');
    const news = [];

    items.forEach((item, index) => {
        const title = item.querySelector('title')?.textContent || '';
        const link = item.querySelector('link')?.textContent || '';
        const description = item.querySelector('description')?.textContent || '';
        const pubDate = item.querySelector('pubDate')?.textContent || '';

        // Clean description (remove HTML tags)
        const cleanDesc = description.replace(/<[^>]*>/g, '').substring(0, 150);

        // Calculate time ago
        const timeAgo = formatTimeAgo(pubDate);

        news.push({
            title,
            link,
            excerpt: cleanDesc,
            source: 'Yahoo Finance',
            timeAgo,
            market: currentMarket,
            impact: index < 3 ? 'high' : 'medium',
            category: 'trading'
        });
    });

    return news;
}

// Format time ago
function formatTimeAgo(dateString) {
    if (!dateString) return 'Unknown';
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    } catch (e) {
        return 'Recently';
    }
}

// Fetch Yahoo Finance RSS feed with CORS proxy
async function fetchYahooNews(market) {
    const feedUrl = yahooFeeds[market];
    if (!feedUrl) return [];

    try {
        // Use CORS proxy (you can replace with your own proxy or use a service)
        const proxyUrl = `https://api.allorigins.win/get?url=${encodeURIComponent(feedUrl)}`;
        const response = await fetch(proxyUrl);
        const data = await response.json();

        if (data.contents) {
            const parsed = parseRSS(data.contents);
            return parsed;
        }
        return [];
    } catch (error) {
        console.error(`Failed to fetch ${market} news:`, error);
        return [];
    }
}

// Fetch all market news
async function fetchAllMarketNews() {
    const newsListEl = document.getElementById('newsList');
    if (newsListEl) {
        newsListEl.innerHTML = '<div class="news-item"><p style="text-align:center;padding:20px;">Loading market news...</p></div>';
    }

    yahooNewsData = [];

    if (currentMarket === 'all' || currentMarket === 'crypto') {
        const cryptoNews = await fetchYahooNews('crypto');
        yahooNewsData.push(...cryptoNews.map(item => ({ ...item, market: 'crypto' })));
    }

    if (currentMarket === 'all' || currentMarket === 'stocks') {
        const stocksNews = await fetchYahooNews('stocks');
        yahooNewsData.push(...stocksNews.map(item => ({ ...item, market: 'stocks' })));
    }

    if (currentMarket === 'all' || currentMarket === 'forex') {
        const forexNews = await fetchYahooNews('forex');
        yahooNewsData.push(...forexNews.map(item => ({ ...item, market: 'forex' })));
    }

    if (currentMarket === 'all' || currentMarket === 'commodities') {
        const commoditiesNews = await fetchYahooNews('commodities');
        yahooNewsData.push(...commoditiesNews.map(item => ({ ...item, market: 'commodities' })));
    }

    if (currentMarket === 'all' || currentMarket === 'economy') {
        const economyNews = await fetchYahooNews('economy');
        yahooNewsData.push(...economyNews.map(item => ({ ...item, market: 'economy' })));
    }

    // Combine with crypto news data
    const allNews = currentMarket === 'crypto' || currentMarket === 'all'
        ? [...newsData, ...yahooNewsData]
        : yahooNewsData;

    renderNews(allNews);
}

function renderNews(newsArray = null) {
    const newsListEl = document.getElementById('newsList');
    const alertsListEl = document.getElementById('alertsList');
    const hotTakesListEl = document.getElementById('hotTakesList');

    if (!newsListEl) return;

    // Use provided array or combine newsData with yahooNewsData
    const allNews = newsArray || (currentMarket === 'crypto' || currentMarket === 'all'
        ? [...newsData, ...yahooNewsData]
        : yahooNewsData);

    // Filter by market
    let marketFiltered = currentMarket === 'all'
        ? allNews
        : allNews.filter(item => item.market === currentMarket || (currentMarket === 'crypto' && newsData.includes(item)));

    // Filter news by category
    const filteredNews = currentNewsCategory === 'all'
        ? marketFiltered
        : marketFiltered.filter(item => item.category === currentNewsCategory);

    // Render main news list
    if (filteredNews.length === 0) {
        newsListEl.innerHTML = '<div class="news-item"><p style="text-align:center;padding:20px;color:var(--text-secondary);">No news available. Try refreshing or selecting a different market.</p></div>';
    } else {
        newsListEl.innerHTML = filteredNews.slice(0, 20).map(item => {
            const impactClass = item.impact === 'critical' ? 'critical' : item.impact === 'high' ? 'high' : '';
            const impactBadge = item.impact === 'critical' ? 'CRITICAL' : item.impact === 'high' ? 'HIGH' : 'MEDIUM';
            const badgeClass = item.impact === 'critical' ? 'critical' : item.impact === 'high' ? 'high' : 'medium';
            const marketBadge = item.market ? `<span class="news-badge category">${item.market.charAt(0).toUpperCase() + item.market.slice(1)}</span>` : '';
            const coinsBadges = item.coins ? item.coins.map(coin => `<span class="news-badge coin">${coin}</span>`).join('') : '';
            const trendIcon = item.trend ? `<span style="font-size:0.8rem; color:var(--text-secondary);">${item.trend}</span>` : '';

            return `
                        <div class="news-item ${impactClass}">
                            <div class="news-item-header">
                                <div class="news-badges">
                                    <span class="news-badge ${badgeClass}">${impactBadge}</span>
                                    ${marketBadge}
                                    <span class="news-badge category">${item.category ? item.category.charAt(0).toUpperCase() + item.category.slice(1) : 'News'}</span>
                                    ${coinsBadges}
                                    ${trendIcon}
                                </div>
                                ${item.impact === 'critical' || item.impact === 'high' ? '<span class="news-hot-icon">⚡</span>' : ''}
                            </div>
                            <h3 class="news-title">
                                <a href="${item.link}" target="_blank" rel="noopener">${item.title}</a>
                            </h3>
                            <p class="news-excerpt">${item.excerpt}</p>
                            <div class="news-meta">
                                <span>${item.source}</span>
                                <span>•</span>
                                <span>${item.timeAgo}</span>
                            </div>
                        </div>
                    `;
        }).join('');
    }

    // Render critical alerts
    if (alertsListEl) {
        const criticalNews = allNews.filter(item => item.impact === 'critical' || item.impact === 'high').slice(0, 3);
        alertsListEl.innerHTML = criticalNews.map(item => {
            const alertClass = item.impact === 'critical' ? '' : 'high';
            return `
                        <div class="news-alert-item ${alertClass}">
                            <div class="news-alert-title">${item.impact.toUpperCase()}: ${item.title}</div>
                            <div class="news-alert-desc">${item.excerpt}</div>
                            <div class="news-alert-tags">
                                <span class="news-alert-tag">news</span>
                                <span style="font-size:0.7rem; color:var(--text-secondary);">${item.timeAgo}</span>
                            </div>
                        </div>
                    `;
        }).join('');
    }

    // Render hot takes
    if (hotTakesListEl) {
        const hotTakes = allNews.filter(item => item.impact === 'critical' || item.impact === 'high').slice(0, 3);
        hotTakesListEl.innerHTML = hotTakes.map(item => {
            const coinsBadges = item.coins ? item.coins.map(coin => `<span class="news-badge coin" style="font-size:0.7rem;">${coin}</span>`).join('') : '';
            return `
                        <div class="news-hot-take-item">
                            <div class="news-hot-take-title">${item.title}</div>
                            <div class="news-hot-take-desc">${item.excerpt}</div>
                            <div class="news-alert-tags" style="margin-top:8px;">
                                ${coinsBadges}
                                <span style="font-size:0.7rem; color:var(--text-secondary);">${item.timeAgo}</span>
                            </div>
                        </div>
                    `;
        }).join('');
    }

    // Update stats
    const hotNewsCount = allNews.filter(item => item.impact === 'critical' || item.impact === 'high').length;
    const alertCount = allNews.filter(item => item.impact === 'critical').length;
    const hotNewsCountEl = document.getElementById('hotNewsCount');
    const alertCountEl = document.getElementById('alertCount');
    const totalNewsCountEl = document.getElementById('totalNewsCount');

    if (hotNewsCountEl) hotNewsCountEl.textContent = hotNewsCount;
    if (alertCountEl) alertCountEl.textContent = alertCount;
    if (totalNewsCountEl) totalNewsCountEl.textContent = allNews.length;
}

function initNewsFilters() {
    const filterBtns = document.querySelectorAll('.news-filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentNewsCategory = btn.dataset.category;
            renderNews();
        });
    });
}

// ============================================
// VIEW COUNTER
// ============================================
function initViewCounter() {
    const viewCountEl = document.getElementById('viewCount');
    if (!viewCountEl) return;

    // Get current count from localStorage
    let totalViews = parseInt(localStorage.getItem('srus_total_views') || '0', 10);

    // Check if this is a new session (not just a refresh)
    const lastVisit = localStorage.getItem('srus_last_visit');
    const now = Date.now();
    const sessionTimeout = 30 * 60 * 1000; // 30 minutes

    // Increment if it's a new visit or session expired
    if (!lastVisit || (now - parseInt(lastVisit, 10)) > sessionTimeout) {
        totalViews += 1;
        localStorage.setItem('srus_total_views', totalViews.toString());
        localStorage.setItem('srus_last_visit', now.toString());
    }

    // Animate the number
    animateViewCount(viewCountEl, totalViews);
}

function animateViewCount(element, targetValue) {
    const duration = 1000; // 1 second
    const startValue = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function (ease-out)
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOut);

        element.textContent = currentValue.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = targetValue.toLocaleString();
        }
    }

    requestAnimationFrame(update);
}

// Start
document.addEventListener('DOMContentLoaded', function () {
    console.log('[DEBUG] DOM loaded, starting init');

    // Force immediate price fetch before init
    fetchOkxTicker().then(() => {
        console.log('[DEBUG] Initial price fetch complete, starting init');
        init();
    }).catch(err => {
        console.error('[DEBUG] Initial price fetch failed:', err);
        // Start init anyway, WebSocket might still work
        init();
    });

    // Force additional price fetch if still no data after 3 seconds
    setTimeout(() => {
        if (!state.price) {
            console.log('[DEBUG] Still no price after 3 seconds, forcing REST fetch again');
            fetchOkxTicker();
        }
    }, 3000);
});
loadSignalHistory();
initSignalPanel();
initNewsFilters();
renderNews();
fetchAllMarketNews(); // Load Yahoo Finance news on page load
initViewCounter();

// Refresh Yahoo Finance news every 5 minutes
setInterval(fetchAllMarketNews, 5 * 60 * 1000);

// ============================================
// PAPER TRADING FUNCTIONALITY
// ============================================
(function initPaperTrading() {
    // Paper Trading State
    let paperPortfolio = {
        balance: 10000,
        totalPnl: 0,
        trades: []
    };

    let paperCurrentTradeType = 'buy';
    let paperCurrentOrderType = 'market';
    let paperCurrentTab = 'open';

    // Load portfolio from sessionStorage
    function loadPaperPortfolio() {
        // Clear old localStorage data to prevent loading old trades
        localStorage.removeItem('srus_paper_portfolio');

        try {
            const saved = sessionStorage.getItem('srus_paper_portfolio');
            if (saved) {
                const parsed = JSON.parse(saved);
                // Validation / Migration
                const balance = parseFloat(parsed.balance);
                paperPortfolio = {
                    balance: !isNaN(balance) && balance > 0 ? balance : 10000,
                    totalPnl: typeof parsed.totalPnl === 'number' ? parsed.totalPnl : 0,
                    trades: Array.isArray(parsed.trades) ? parsed.trades : []
                };
            }
        } catch (e) {
            console.error('Failed to load paper portfolio:', e);
            // Reset to default on error
            paperPortfolio = {
                balance: 10000,
                totalPnl: 0,
                trades: []
            };
        }

        // Double safety check
        if (isNaN(paperPortfolio.balance)) {
            paperPortfolio.balance = 10000;
        }
    }

    // Save portfolio to sessionStorage
    function savePaperPortfolio() {
        try {
            sessionStorage.setItem('srus_paper_portfolio', JSON.stringify(paperPortfolio));
        } catch (e) {
            console.error('Failed to save paper portfolio:', e);
        }
    }

    // Initialize
    loadPaperPortfolio();

    // Hoist DOM elements to top scope to avoid Temporal Dead Zone (ReferenceError)
    const amountInput = document.getElementById('paperAmount');
    const limitPriceInput = document.getElementById('paperLimitPrice');
    const submitBtn = document.getElementById('paperSubmitBtn');

    // Force initial balance display
    const balanceEl = document.getElementById('paperBalance');
    if (balanceEl && paperPortfolio.balance) {
        balanceEl.textContent = `$${paperPortfolio.balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    updatePaperUI();

    // Global functions for inline onclick handlers (most reliable)
    window.setPaperOrderType = function (type, clickedBtn) {
        console.log('[DEBUG] setPaperOrderType called:', type, 'clickedBtn:', clickedBtn);

        // Update tabs
        const parent = clickedBtn.parentElement;
        if (parent) {
            Array.from(parent.children).forEach(child => child.classList.remove('active'));
        }
        clickedBtn.classList.add('active');

        paperCurrentOrderType = type;

        const limitContainer = document.getElementById('limitPriceContainer');

        if (limitContainer) {
            limitContainer.style.display = type === 'limit' ? 'block' : 'none';
        }

        // Note: marketPriceContainer does not exist in HTML, logic removed.

        calculatePaperOrder();
    };

    window.paperSetOrderType = window.setPaperOrderType;

    window.paperSetTradeType = function (type, clickedBtn) {
        console.log('[DEBUG] paperSetTradeType called:', type);
        document.querySelectorAll('.paper-trade-btn').forEach(b => b.classList.remove('active'));
        clickedBtn.classList.add('active');
        paperCurrentTradeType = type;
        calculatePaperOrder();
    };

    // Event Delegation for other buttons (percent buttons, etc.)
    document.addEventListener('click', function (e) {

        // 3. Position Tabs (Open/Pending/Closed) - Support both onclick and click
        const posTab = e.target.closest('.paper-positions-tab');
        if (posTab) {
            const tabName = posTab.getAttribute('onclick') ?
                (posTab.getAttribute('onclick').match(/switchPaperTab\('(\w+)'\)/) || [])[1] :
                posTab.dataset.tab;
            if (tabName) {
                document.querySelectorAll('.paper-positions-tab').forEach(t => t.classList.remove('active'));
                posTab.classList.add('active');
                paperCurrentTab = tabName;
                renderPaperPositions();
                return;
            }
        }

        // 4. Submit Button (New Solid Buttons)
        if (e.target.id === 'paperBuyBtn') {
            e.preventDefault();
            paperCurrentTradeType = 'buy';
            executePaperTrade();
            return;
        }
        if (e.target.id === 'paperSellBtn') {
            e.preventDefault();
            paperCurrentTradeType = 'sell';
            executePaperTrade();
            return;
        }
    });

    // Phemex Widget Tab Logic (Limit vs Market) - moved to onclick handlers in HTML for reliability

    // Amount input updates
    if (amountInput) {
        amountInput.addEventListener('input', () => {
            calculatePaperOrder();
        });
    }

    // Limit Price updates
    if (limitPriceInput) {
        limitPriceInput.addEventListener('input', () => {
            calculatePaperOrder();
        });
    }

    // Initial calculation
    setTimeout(() => {
        calculatePaperOrder();
    }, 1000);

    // Global functions for percent and price offset buttons
    window.paperSetPercent = function (percent) {
        console.log('[DEBUG] paperSetPercent called:', percent);
        const amountInput = document.getElementById('paperAmount');
        if (state.price && amountInput) {
            const availableBalance = paperPortfolio.balance;
            const usdAmount = availableBalance * (percent / 100);
            amountInput.value = usdAmount.toFixed(2);
            calculatePaperOrder();
        }
    };

    window.paperSetPriceOffset = function (offset) {
        const limitPriceInput = document.getElementById('paperLimitPrice');
        if (state.price && limitPriceInput) {
            const newPrice = state.price * (1 + offset / 100);
            limitPriceInput.value = newPrice.toFixed(2);
            updatePaperOrderSummary();
            updatePaperSubmitButton();
        }
    };

    // Reset button
    const resetBtn = document.getElementById('paperResetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (confirm('Reset your paper trading portfolio? This will clear all trades and reset balance to $10,000.')) {
                paperPortfolio = {
                    balance: 10000,
                    totalPnl: 0,
                    trades: []
                };
                localStorage.removeItem('srus_paper_portfolio');
                savePaperPortfolio();
                updatePaperUI();
                renderPaperPositions();
            }
        });
    }

    // Execute trade function (global)
    window.executePaperTrade = function () {
        console.log('executePaperTrade called');

        // Ensure state exists
        if (!state || !state.price) {
            console.error('State or Price unavailable:', state);
            alert('Waiting for price data... (Check Console)');
            return;
        }

        const amountInput = document.getElementById('paperAmount');
        const limitPriceInput = document.getElementById('paperLimitPrice');

        const usdValue = parseFloat(amountInput.value);
        console.log('Trade Values:', { usdValue, price: state.price, orderType: paperCurrentOrderType });

        if (!usdValue || usdValue <= 0) {
            alert('Please enter a valid USD amount');
            return;
        }

        // Calculate BTC amount from USD
        const executionPrice = paperCurrentOrderType === 'limit'
            ? parseFloat(limitPriceInput.value)
            : state.price;

        console.log('Execution Price:', executionPrice);

        if (!executionPrice) {
            alert('Invalid price');
            return;
        }

        const amount = usdValue / executionPrice;

        // Check balance
        // Simple check: do we have enough cash?
        // (Ignoring leverage for safety check, or assume 1x)
        if (usdValue > paperPortfolio.balance) {
            alert(`Insufficient balance. Available: ${priceFormatter.format(paperPortfolio.balance)}`);
            return;
        }

        const trade = {
            id: Date.now(),
            symbol: state.symbol,
            type: paperCurrentTradeType, // 'buy' or 'sell'
            orderType: paperCurrentOrderType, // 'market' or 'limit'
            price: executionPrice,
            amount: amount, // Stored in BTC
            entryValueUsd: usdValue,
            status: paperCurrentOrderType === 'market' ? 'open' : 'pending',
            limitPrice: paperCurrentOrderType === 'limit' ? executionPrice : null,
            timestamp: new Date().toISOString()
        };


        console.log('Creating Trade:', trade);

        paperPortfolio.trades.push(trade);
        savePaperPortfolio();

        // Clear inputs
        // if (amountInput) amountInput.value = ''; // Keep for convenience testing
        // if (limitPriceInput) limitPriceInput.value = '';

        updatePaperUI();
        renderPaperPositions();
        updatePaperOrderSummary();

        // Show success feedback
        const submitBtn = document.getElementById('paperSubmitBtn');
        if (submitBtn) {
            const btnOriginalText = submitBtn.textContent;
            submitBtn.textContent = "Order Placed!";
            setTimeout(() => {
                submitBtn.textContent = btnOriginalText;
                updatePaperSubmitButton();
            }, 1500);
        }

        // Send to Discord Leaderboard
        const user = getUsername();
        sendToDiscord({
            username: "Snipers Leaderboard",
            embeds: [{
                title: `🔔 New Trade Opened`,
                color: 3447003, // Blue
                description: `**${user}** opened a **${trade.type.toUpperCase()}** on **${trade.symbol}**`,
                fields: [
                    { name: "Entry Price", value: `$${trade.price.toLocaleString()}`, inline: true },
                    { name: "Size", value: `${trade.amount} ${trade.symbol}`, inline: true },
                    { name: "Order Type", value: trade.orderType.toUpperCase(), inline: true }
                ],
                footer: { text: "Paper Trading Competition" },
                timestamp: new Date().toISOString()
            }]
        });
    };

    // Update order summary
    function updatePaperOrderSummary() {
        const amountInput = document.getElementById('paperAmount');
        const limitPriceInput = document.getElementById('paperLimitPrice');
        const amount = parseFloat(amountInput?.value || '0');
        const summaryEl = document.getElementById('paperOrderSummary');
        const priceEl = document.getElementById('paperOrderPrice');
        const amountEl = document.getElementById('paperOrderAmount');
        const totalEl = document.getElementById('paperOrderTotal');

        if (!amount || amount <= 0) {
            if (summaryEl) summaryEl.style.display = 'none';
            return;
        }

        const price = paperCurrentOrderType === 'market'
            ? state.price
            : parseFloat(limitPriceInput?.value || state.price || 0);

        if (summaryEl) summaryEl.style.display = 'block';
        if (priceEl) priceEl.textContent = `$${price.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        if (amountEl) amountEl.textContent = `${amount.toFixed(8)} ${state.symbol}`;
        if (totalEl) totalEl.textContent = `$${(amount * price).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
    }

    // Update submit button
    function updatePaperSubmitButton() {
        const amount = parseFloat(amountInput?.value || '0');
        const currentPrice = state && state.price ? state.price : 0;
        const price = paperCurrentOrderType === 'market'
            ? currentPrice
            : parseFloat(limitPriceInput?.value || '0');
        const totalCost = amount * price;

        const isValid = amount > 0 &&
            (paperCurrentOrderType === 'market' || (price > 0 && price !== currentPrice)) &&
            (paperCurrentTradeType === 'sell' || totalCost <= paperPortfolio.balance) &&
            price > 0;

        if (submitBtn) {
            submitBtn.disabled = !isValid;
            submitBtn.textContent = paperCurrentOrderType === 'market'
                ? (paperCurrentTradeType === 'buy' ? 'Buy Market' : 'Sell Market')
                : (paperCurrentTradeType === 'buy' ? 'Place Buy Limit' : 'Place Sell Limit');
            submitBtn.className = `paper-submit-btn ${paperCurrentTradeType}`;
        }
    }

    // Update UI
    function updatePaperUI() {
        // Safety check
        if (!paperPortfolio || !paperPortfolio.trades) return;

        const balanceEl = document.getElementById('paperBalance');
        const equityEl = document.getElementById('paperEquity');
        const realizedEl = document.getElementById('paperRealizedPnL');
        const unrealizedEl = document.getElementById('paperUnrealizedPnL');
        const availEl = document.getElementById('paperAvailableAmount');

        const currentPrice = state.price || 0;
        let unrealizedPnL = 0;

        // Calculate PnL
        paperPortfolio.trades.forEach(t => {
            if (t.status === 'open') {
                if (t.type === 'buy') {
                    unrealizedPnL += (currentPrice - t.price) * t.amount;
                } else {
                    unrealizedPnL += (t.price - currentPrice) * t.amount;
                }
            }
        });

        const equity = paperPortfolio.balance + unrealizedPnL;

        // Update text
        if (balanceEl) balanceEl.textContent = priceFormatter.format(paperPortfolio.balance);
        if (equityEl) equityEl.textContent = priceFormatter.format(equity);

        if (realizedEl) {
            realizedEl.textContent = (paperPortfolio.totalPnl >= 0 ? '+' : '') + priceFormatter.format(paperPortfolio.totalPnl);
            realizedEl.style.color = paperPortfolio.totalPnl >= 0 ? 'var(--accent-green)' : 'var(--accent-purple)';
        }

        if (unrealizedEl) {
            unrealizedEl.textContent = (unrealizedPnL >= 0 ? '+' : '') + priceFormatter.format(unrealizedPnL);
            unrealizedEl.style.color = unrealizedPnL >= 0 ? 'var(--accent-green)' : 'var(--accent-purple)';
        }

        // Update Available (USD)
        // Since our 'balance' tracks cash, that is the available amount.
        if (availEl) {
            availEl.textContent = `Available: ${priceFormatter.format(paperPortfolio.balance)}`;
        }

        // Update counts
        const openCount = paperPortfolio.trades.filter(t => t.status === 'open').length;
        const pendingCount = paperPortfolio.trades.filter(t => t.status === 'pending').length;
        const closedCount = paperPortfolio.trades.filter(t => t.status === 'closed').length;

        const openCountEl = document.getElementById('openPosCount');
        const pendingCountEl = document.getElementById('pendingCount');
        const closedCountEl = document.getElementById('closedCount');

        if (openCountEl) openCountEl.textContent = openCount;
        if (pendingCountEl) pendingCountEl.textContent = pendingCount;
        if (closedCountEl) closedCountEl.textContent = closedCount;

        updatePaperSubmitButton();
        checkPendingOrders();
    }

    // Check pending orders
    function checkPendingOrders() {
        const pendingOrders = paperPortfolio.trades.filter(t => t.status === 'pending' && t.symbol === state.symbol);
        if (pendingOrders.length === 0) return;

        let stateChanged = false;
        pendingOrders.forEach(trade => {
            if (!trade.limitPrice || !state.price) return;

            // Improved logic:
            // Buy Limit: execute if current price <= limit price
            // Sell Limit: execute if current price >= limit price
            const shouldExecute = trade.type === 'buy'
                ? state.price <= trade.limitPrice
                : state.price >= trade.limitPrice;

            if (shouldExecute) {
                trade.status = 'open';
                trade.price = trade.limitPrice; // Execute at limit price (or better)
                trade.entryTime = new Date().toISOString();

                // Deduct balance now if we haven't already (depending on margin model)
                // In executePaperTrade we didn't deduct for pending. So do it now.
                const totalCost = trade.amount * trade.price;
                // For simplicity in this demo, just deduct cost for both long and short to simulate margin usage
                if (paperPortfolio.balance >= totalCost) {
                    paperPortfolio.balance -= totalCost;
                } else {
                    // Failed to fill due to balance? Cancel it?
                    // For now let's just allow it or set negative balance (margin call sim)
                    paperPortfolio.balance -= totalCost;
                }

                stateChanged = true;

                // Notify user (simple toast or console for now)
                console.log(`Order Filled: ${trade.type.toUpperCase()} ${trade.symbol} at ${trade.price}`);
            }
        });

        if (stateChanged) {
            savePaperPortfolio();
            renderPaperPositions(); // Re-render to show moved trades
            updatePaperUI();
        }
    }

    // Render positions
    function renderPaperPositions() {
        const contentEl = document.getElementById('paperPositionsContent');
        if (!contentEl) return;

        let positions = [];
        if (paperCurrentTab === 'open') {
            positions = paperPortfolio.trades.filter(t => t.status === 'open' && t.symbol === state.symbol);
        } else if (paperCurrentTab === 'pending') {
            positions = paperPortfolio.trades.filter(t => t.status === 'pending' && t.symbol === state.symbol);
        } else {
            positions = paperPortfolio.trades.filter(t => t.status === 'closed' && t.symbol === state.symbol);
        }

        // Update counts
        const openC = paperPortfolio.trades.filter(t => t.status === 'open').length;
        const pendingC = paperPortfolio.trades.filter(t => t.status === 'pending').length;
        const closedC = paperPortfolio.trades.filter(t => t.status === 'closed').length;

        const openCountEl = document.getElementById('openPosCount');
        const pendingCountEl = document.getElementById('pendingCount');
        const closedCountEl = document.getElementById('closedCount');

        if (openCountEl) openCountEl.textContent = openC;
        if (pendingCountEl) pendingCountEl.textContent = pendingC;
        if (closedCountEl) closedCountEl.textContent = closedC;


        if (positions.length === 0) {
            contentEl.innerHTML = `
                <div class="paper-empty-state">
                    <p>No ${paperCurrentTab === 'open' ? 'open positions' : paperCurrentTab === 'pending' ? 'pending orders' : 'closed trades'}</p>
                </div>
            `;
            return;
        }

        contentEl.innerHTML = positions.map(trade => {
            const pnl = trade.status === 'open'
                ? (trade.type === 'buy' ? (state.price - trade.price) * trade.amount : (trade.price - state.price) * trade.amount)
                : (trade.pnl || 0);

            if (trade.status === 'open') {
                return `
                    <div class="paper-position-item ${trade.type === 'sell' ? 'short' : ''}">
                        <div class="paper-position-row">
                            <div>
                                <div class="paper-position-label">Type</div>
                                <div class="paper-position-value" style="color: ${trade.type === 'buy' ? 'var(--accent-green)' : 'var(--accent-purple)'}">
                                    ${trade.type === 'buy' ? 'LONG' : 'SHORT'}
                                </div>
                            </div>
                            <div>
                                <div class="paper-position-label">Size</div>
                                <div class="paper-position-value">${trade.amount.toFixed(8)} ${trade.symbol}</div>
                            </div>
                            <div>
                                <div class="paper-position-label">Entry</div>
                                <div class="paper-position-value">$${trade.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                            </div>
                            <div>
                                <div class="paper-position-label">P&L</div>
                                <div class="paper-position-value" style="color: ${pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-purple)'}">
                                    ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}
                                </div>
                            </div>
                        </div>
                        <div class="paper-position-actions">
                            <button class="paper-action-btn" onclick="closePaperTrade(${trade.id})">Close</button>
                        </div>
                    </div>
                `;
            } else if (trade.status === 'pending') {
                const distance = ((state.price - trade.limitPrice) / trade.limitPrice) * 100;
                return `
                    <div class="paper-position-item" style="border-left-color: var(--accent-green);">
                        <div class="paper-position-row">
                            <div>
                                <div class="paper-position-label">Type</div>
                                <div class="paper-position-value">${trade.type === 'buy' ? 'Buy Limit' : 'Sell Limit'}</div>
                            </div>
                            <div>
                                <div class="paper-position-label">Size</div>
                                <div class="paper-position-value">${trade.amount.toFixed(8)} ${trade.symbol}</div>
                            </div>
                            <div>
                                <div class="paper-position-label">Limit Price</div>
                                <div class="paper-position-value">$${trade.limitPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                            </div>
                            <div>
                                <div class="paper-position-label">Distance</div>
                                <div class="paper-position-value">${distance.toFixed(2)}%</div>
                            </div>
                        </div>
                        <div class="paper-position-actions">
                            <button class="paper-action-btn" onclick="cancelPaperOrder(${trade.id})">Cancel</button>
                        </div>
                    </div>
                `;
            } else {
                return `
                    <div class="paper-position-item" style="border-left-color: var(--text-secondary);">
                        <div class="paper-position-row">
                            <div>
                                <div class="paper-position-label">Type</div>
                                <div class="paper-position-value">${trade.type === 'buy' ? 'LONG' : 'SHORT'}</div>
                            </div>
                            <div>
                                <div class="paper-position-label">Size</div>
                                <div class="paper-position-value">${trade.amount.toFixed(8)} ${trade.symbol}</div>
                            </div>
                            <div>
                                <div class="paper-position-label">Entry</div>
                                <div class="paper-position-value">$${trade.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                            </div>
                            <div>
                                <div class="paper-position-label">Closed P&L</div>
                                <div class="paper-position-value" style="color: ${pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-purple)'}">
                                    ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }).join('');
    }

    // Close Trade Function
    window.closePaperTrade = function (id) {
        try {
            const tradeIndex = paperPortfolio.trades.findIndex(t => t.id == id);
            if (tradeIndex === -1) {
                console.error('Trade not found:', id);
                return;
            }

            const trade = paperPortfolio.trades[tradeIndex];

            if (!state || !state.price) {
                console.error('Price data not available:', state);
                alert('Price data not available. Please wait for market data to load.');
                return;
            }

            const currentPrice = state.price;
            const pnl = trade.type === 'buy'
                ? (currentPrice - trade.price) * trade.amount
                : (trade.price - currentPrice) * trade.amount;

            trade.status = 'closed';
            trade.exitPrice = currentPrice;
            trade.exitTime = new Date().toISOString();
            trade.pnl = pnl;

            paperPortfolio.balance += (trade.amount * trade.price) + pnl;
            paperPortfolio.totalPnl += pnl;

            savePaperPortfolio();
            updatePaperUI();
            renderPaperPositions();

            const user = getUsername();
            try {
                sendToDiscord({
                    username: "Snipers Leaderboard",
                    embeds: [{
                        title: `💰 Trade Closed (${pnl >= 0 ? 'WIN' : 'LOSS'})`,
                        color: pnl >= 0 ? 5763719 : 15548997,
                        description: `**${user}** closed **${trade.symbol}** for **${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}**`,
                        fields: [
                            { name: "Return", value: `${((pnl / (trade.amount * trade.price)) * 100).toFixed(2)}%`, inline: true },
                            { name: "Total PnL", value: `$${paperPortfolio.totalPnl.toFixed(2)}`, inline: true }
                        ],
                        timestamp: new Date().toISOString()
                    }]
                });
            } catch (e) { console.error('Discord error:', e); }
        } catch (error) {
            console.error('Error closing trade:', error);
            alert('Failed to close trade. Please try again.');
        }
    };

    // Calculate Paper Order (for order summary)
    window.calculatePaperOrder = function () {
        console.log('[DEBUG] calculatePaperOrder called, paperCurrentOrderType:', paperCurrentOrderType, 'state.price:', state.price);
        let price;
        if (paperCurrentOrderType === 'limit') {
            const limitPriceEl = document.getElementById('paperLimitPrice');
            price = parseFloat(limitPriceEl?.value) || 0;
        } else {
            price = state.price || 0;
        }

        const amountEl = document.getElementById('paperAmount');
        const amount = parseFloat(amountEl?.value) || 0;
        const qty = price > 0 ? amount / price : 0;

        const priceEl = document.getElementById('paperOrderPrice');
        const qtyEl = document.getElementById('paperOrderAmount');
        const totalEl = document.getElementById('paperOrderTotal');

        if (priceEl) priceEl.textContent = price > 0 ? `$${priceFormatter.format(price)}` : '--';
        if (qtyEl) qtyEl.textContent = qty > 0 ? `${qty.toFixed(6)} ${state.symbol}` : '0 ' + (state.symbol || 'BTC');
        if (totalEl) totalEl.textContent = amount > 0 ? `$${priceFormatter.format(amount)}` : '$0.00';

        // Update market price display
        const marketPriceEl = document.getElementById('paperMarketPrice');
        if (marketPriceEl && state.price) {
            marketPriceEl.value = state.price.toFixed(2);
        }
    };

    // Open Paper Position (simplified version matching provided code)
    window.openPaperPosition = function (side) {
        console.log('[DEBUG] openPaperPosition called with side:', side);
        console.log('[DEBUG] paperCurrentOrderType:', paperCurrentOrderType);
        console.log('[DEBUG] state.price:', state.price);

        const amountEl = document.getElementById('paperAmount');
        const amount = parseFloat(amountEl?.value) || 0;

        let price;
        if (paperCurrentOrderType === 'limit') {
            const limitPriceEl = document.getElementById('paperLimitPrice');
            price = parseFloat(limitPriceEl?.value) || 0;
        } else {
            price = state.price || 0;
        }

        if (!price || price <= 0) {
            alert("Market data is still loading. Please wait for current price to appear before placing a trade.");
            return;
        }

        if (!amount || amount <= 0) {
            alert("Please enter a valid trade amount.");
            return;
        }

        if (amount > paperPortfolio.balance) {
            alert(`Insufficient Balance. Available: ${priceFormatter.format(paperPortfolio.balance)}`);
            return;
        }

        paperPortfolio.balance -= amount;
        const qty = amount / price;

        const trade = {
            id: Date.now(),
            symbol: state.symbol,
            type: side === 'LONG' ? 'buy' : 'sell',
            side: side,
            entry: price,
            price: price,
            qty: qty,
            amount: qty,
            margin: amount,
            status: 'open',
            entryTime: new Date().toISOString(),
            orderType: paperCurrentOrderType
        };

        paperPortfolio.trades.push(trade);

        savePaperPortfolio();
        updatePaperUI();
        renderPaperPositions();

        // Reset amount input
        if (amountEl) amountEl.value = '1000';
        calculatePaperOrder();


    };

    // Switch Paper Tab
    window.switchPaperTab = function (tab) {
        paperCurrentTab = tab;
        const tabOpen = document.getElementById('tabOpen');
        const tabHistory = document.getElementById('tabHistory');

        if (tabOpen) tabOpen.classList.toggle('active', tab === 'open');
        if (tabHistory) tabHistory.classList.toggle('active', tab === 'history');

        renderPaperPositions();
    };

    // Cancel Order Function
    window.cancelPaperOrder = function (id) {
        try {
            const tradeIndex = paperPortfolio.trades.findIndex(t => t.id == id);
            if (tradeIndex === -1) {
                console.error('Order not found:', id);
                return;
            }

            const trade = paperPortfolio.trades[tradeIndex];
            const cost = trade.amount * trade.price;
            paperPortfolio.balance += cost;

            paperPortfolio.trades.splice(tradeIndex, 1);

            savePaperPortfolio();
            updatePaperUI();
            renderPaperPositions();
        } catch (error) {
            console.error('Error canceling order:', error);
            alert('Failed to cancel order. Please try again.');
        }
    };

    // Hook into price updates to refresh paper UI
    if (window.updatePriceDisplay) {
        const originalUpdatePriceDisplay = window.updatePriceDisplay;
        window.updatePriceDisplay = function (price, pctChange) {
            originalUpdatePriceDisplay(price, pctChange);
            updatePaperUI();
            if (paperCurrentTab === 'open') {
                renderPaperPositions();
            }
        };
    }

    // Hook into pair changes
    if (window.setPair) {
        const originalSetPair = window.setPair;
        window.setPair = function (symbol) {
            originalSetPair(symbol);
        };
    }

    // Fallback Interval for UI updates
    setInterval(() => {
        updatePaperUI();
        if (paperCurrentTab === 'open') {
            renderPaperPositions();
        }
    }, 1000);



    // ============================================
    // 3-DAY FREE TRIAL POPUP
    // ============================================
    function initTrialPopup() {
        const popup = document.getElementById('freeTrialPopup');
        if (!popup) return;

        setTimeout(() => {
            popup.classList.remove('hidden');
            requestAnimationFrame(() => {
                popup.classList.add('show');
            });
        }, 15000); // 15 seconds
    }

    function closeTrialPopup() {
        const popup = document.getElementById('freeTrialPopup');
        if (popup) {
            popup.classList.remove('show');
            setTimeout(() => {
                popup.classList.add('hidden');
            }, 400);
        }
    }
    window.closeTrialPopup = closeTrialPopup;

    // Initialize Popup
    document.addEventListener('DOMContentLoaded', initTrialPopup);


    // ============================================
    // LEADERBOARD LOGIC
    // ============================================
    // Placeholder for now, static HTML handles most.
    // Could add logic here to fetch top traders from a real backend later.

    function renderPaperPositions() {
        const contentEl = document.getElementById('paperPositionsList');
        if (!contentEl) return;

        let positions = [];
        if (paperCurrentTab === 'open') {
            positions = paperPortfolio.trades.filter(t => t.status === 'open' || t.status === 'pending');
        } else {
            positions = paperPortfolio.trades.filter(t => t.status === 'closed');
        }
        // sort by newest
        positions.sort((a, b) => b.id - a.id);

        if (positions.length === 0) {
            contentEl.innerHTML = `
                        <div class="paper-empty-state">
                            <p>No ${paperCurrentTab === 'open' ? 'open positions' : paperCurrentTab === 'pending' ? 'pending orders' : 'closed trades'}</p>
                            <p style="font-size: 0.85rem; margin-top: 8px;">Place a trade to get started</p>
                </div>
                    `;
            return;
        }

        contentEl.innerHTML = positions.map(trade => {
            const pnl = trade.status === 'open'
                ? (trade.type === 'buy' ? (state.price - trade.price) * trade.amount : (trade.price - state.price) * trade.amount)
                : (trade.pnl || 0);

            if (trade.status === 'open') {
                return `
                            <div class="paper-position-item ${trade.type === 'sell' ? 'short' : ''}">
                                <div class="paper-position-row">
                                    <div>
                                        <div class="paper-position-label">Type</div>
                                        <div class="paper-position-value" style="color: ${trade.type === 'buy' ? 'var(--accent-green)' : 'var(--accent-purple)'}">
                                            ${trade.type === 'buy' ? 'LONG' : 'SHORT'}
                                        </div>
                                    </div>
                                    <div>
                                        <div class="paper-position-label">Size</div>
                                        <div class="paper-position-value">${trade.amount.toFixed(8)} ${trade.symbol}</div>
                                    </div>
                                    <div>
                                        <div class="paper-position-label">Entry</div>
                                        <div class="paper-position-value">$${trade.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                                    </div>
                                    <div>
                                        <div class="paper-position-label">P&L</div>
                                        <div class="paper-position-value" style="color: ${pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-purple)'}">
                                            ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}
                                        </div>
                                    </div>
                                </div>
                                <div class="paper-position-actions">
                                    <button class="paper-action-btn" onclick="closePaperTrade(${trade.id})">Close</button>
                                </div>
                            </div>
                        `;
            } else if (trade.status === 'pending') {
                const distance = ((state.price - trade.limitPrice) / trade.limitPrice) * 100;
                return `
                            <div class="paper-position-item" style="border-left-color: var(--accent-green);">
                                <div class="paper-position-row">
                                    <div>
                                        <div class="paper-position-label">Type</div>
                                        <div class="paper-position-value">${trade.type === 'buy' ? 'Buy Limit' : 'Sell Limit'}</div>
                                    </div>
                                    <div>
                                        <div class="paper-position-label">Size</div>
                                        <div class="paper-position-value">${trade.amount.toFixed(8)} ${trade.symbol}</div>
                                    </div>
                                    <div>
                                        <div class="paper-position-label">Limit Price</div>
                                        <div class="paper-position-value">$${trade.limitPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                                    </div>
                                    <div>
                                        <div class="paper-position-label">Distance</div>
                                        <div class="paper-position-value">${distance.toFixed(2)}%</div>
                                    </div>
                                </div>
                                <div class="paper-position-actions">
                                    <button class="paper-action-btn" onclick="cancelPaperOrder(${trade.id})">Cancel</button>
                                </div>
                            </div>
                        `;
            } else {
                return `
                <div class="paper-position-item closed">
                    <div class="paper-position-row">
                        <div>
                            <div class="paper-position-label">Type</div>
                            <div class="paper-position-value" style="color: ${trade.type === 'buy' ? 'var(--accent-green)' : 'var(--accent-purple)'}">
                                ${trade.type === 'buy' ? 'LONG' : 'SHORT'}
                            </div>
                        </div>
                        <div>
                            <div class="paper-position-label">Size</div>
                            <div class="paper-position-value">${trade.amount.toFixed(8)} ${trade.symbol}</div>
                        </div>
                        <div>
                             <div class="paper-position-label">Entry</div>
                             <div class="paper-position-value">$${trade.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                        </div>
                        <div>
                             <div class="paper-position-label">Closed P&L</div>
                             <div class="paper-position-value" style="color: ${pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-purple)'}">
                                 ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}
                             </div>
                        </div>
                    </div>
                </div>
            `;
            }
        }).join('');
    }

})();



// ============================================
// 3-DAY FREE TRIAL POPUP
// ============================================
function initTrialPopup() {
    const popup = document.getElementById('freeTrialPopup');
    if (!popup) return;

    // Check if already seen/closed (optional, for now show every time as per request or use sessionStorage)
    // User asked to modify it to appear 15s after load.
    // If we want it to not annoy, maybe check sessionStorage. But for verification, let's force it.

    setTimeout(() => {
        popup.classList.remove('hidden');
        // Small delay to allow display:block to apply before opacity transition
        requestAnimationFrame(() => {
            popup.classList.add('show');
        });
    }, 15000); // 15 seconds
}

function closeTrialPopup() {
    const popup = document.getElementById('freeTrialPopup');
    if (popup) {
        popup.classList.remove('show');
        setTimeout(() => {
            popup.classList.add('hidden');
        }, 400); // match css transition
    }
}
window.closeTrialPopup = closeTrialPopup;

// Initialize Popup
document.addEventListener('DOMContentLoaded', initTrialPopup);





// ====== ARCADE GAME ======
(function initArcadeGame() {
    const gameCanvas = document.getElementById('gameCanvas');
    if (!gameCanvas) return;
    const gameCtx = gameCanvas.getContext('2d');
    const gameStatusEl = document.getElementById('game-status');
    const gameScoreEl = document.getElementById('gameScore');
    const gameLivesEl = document.getElementById('gameLives');
    const btnLong = document.getElementById('btnLong');
    const btnShort = document.getElementById('btnShort');
    const btnQuit = document.getElementById('btn-quit');
    const menuOverlay = document.getElementById('menu-overlay');
    const endOverlay = document.getElementById('end-overlay');
    const endTitle = document.getElementById('end-title');
    const endMsg = document.getElementById('end-msg');
    const btnStart = document.getElementById('btn-start');
    const btnRetry = document.getElementById('btn-retry');

    gameCanvas.width = 560;
    gameCanvas.height = 200;

    let gameCredits = 1000;
    let gameLives = 3;
    let gameStreak = 0;
    let gameCandles = [];

    const MAX_VISIBLE_CANDLES = 24;
    const CANDLE_WIDTH = 20;
    const CANDLE_SPACING = 2;

    let gameState = 'MENU';
    let currentRoundCandle = null;
    let roundTimer = 0;
    const ROUND_LENGTH = 5;
    const WINNING_SCORE = 2000;

    let gamePrice = 2500;
    for (let i = 0; i < MAX_VISIBLE_CANDLES; i++) {
        generateFakeCandle(true);
    }

    // Make game functions globally accessible (will be assigned after function definitions)
    // Functions are defined below, we'll assign them to window after they're created

    function gameLoop() {
        if (gameState !== 'GAMEOVER' && gameState !== 'MENU') {
            updateGame();
            drawGame();
        }
        requestAnimationFrame(gameLoop);
    }
    gameLoop();

    // Make game functions globally accessible for inline onclick handlers
    window.gameStart = startGame;
    window.gamePlaceBet = placeBet;
    window.gameQuit = function () {
        if (confirm("QUIT GAME? ALL PROGRESS WILL BE LOST.")) {
            quitToMenu();
        }
    };

    function updateGame() {
        let last = gameCandles[gameCandles.length - 1];
        if (!last) return;

        let move = (Math.random() - 0.5) * 10;
        last.close += move;

        if (last.close > last.high) last.high = last.close;
        if (last.close < last.low) last.low = last.close;

        if (gameState === 'RUNNING') {
            roundTimer -= 1 / 60;
            if (gameStatusEl) gameStatusEl.innerText = `CANDLE CLOSING IN: ${Math.ceil(roundTimer)}s`;
            if (roundTimer <= 0) {
                endRound();
            }
        }
    }

    function startGame() {
        gameCredits = 1000;
        gameLives = 3;
        gameStreak = 0;
        if (gameScoreEl) gameScoreEl.innerText = gameCredits;
        updateLivesDisplay();

        gameCandles = [];
        gamePrice = 2500;
        for (let i = 0; i < MAX_VISIBLE_CANDLES; i++) {
            generateFakeCandle(true);
        }

        if (menuOverlay) menuOverlay.style.display = 'none';
        if (endOverlay) endOverlay.style.display = 'none';
        if (btnQuit) btnQuit.style.display = 'block';

        gameState = 'BETTING';
        if (gameStatusEl) {
            gameStatusEl.innerText = "PLACE YOUR BET";
            gameStatusEl.className = "game-wait-text";
        }
        if (btnLong) btnLong.disabled = false;
        if (btnShort) btnShort.disabled = false;
    }

    function quitToMenu() {
        gameState = 'MENU';
        if (menuOverlay) menuOverlay.style.display = 'flex';
        if (endOverlay) endOverlay.style.display = 'none';
        if (btnQuit) btnQuit.style.display = 'none';
    }

    function placeBet(direction) {
        if (gameState !== 'BETTING') return;

        gameState = 'RUNNING';
        roundTimer = ROUND_LENGTH;

        // Disable buttons explicitly
        if (btnLong) btnLong.disabled = true;
        if (btnShort) btnShort.disabled = true;

        if (gameStatusEl) {
            gameStatusEl.innerText = "ROUND STARTED...";
            gameStatusEl.className = "game-wait-text";
        }

        let prevClose = gameCandles[gameCandles.length - 1].close;

        currentRoundCandle = {
            open: prevClose,
            close: prevClose,
            high: prevClose,
            low: prevClose,
            direction: direction
        };

        gameCandles.push(currentRoundCandle);
        if (gameCandles.length > MAX_VISIBLE_CANDLES) {
            gameCandles.shift();
        }

        // Force immediate draw to show entry line
        drawGame();
    }

    function generateFakeCandle(isComplete) {
        let prev = gameCandles.length > 0 ? gameCandles[gameCandles.length - 1].close : 2500;
        let open = prev;
        let close = open + (Math.random() - 0.5) * 30;
        let high = Math.max(open, close) + Math.random() * 5;
        let low = Math.min(open, close) - Math.random() * 5;

        gameCandles.push({ open, close, high, low, complete: true });

        if (gameCandles.length > MAX_VISIBLE_CANDLES) {
            gameCandles.shift();
        }
    }

    function endRound() {
        gameState = 'RESULT';
        let c = currentRoundCandle;
        let isGreen = c.close > c.open;
        let win = false;

        if (c.direction === 'LONG' && isGreen) win = true;
        if (c.direction === 'SHORT' && !isGreen) win = true;

        if (win) {
            handleWin();
        } else {
            handleLoss();
        }

        if (gameState !== 'GAMEOVER') {
            setTimeout(() => {
                gameState = 'BETTING';
                if (btnLong) btnLong.disabled = false;
                if (btnShort) btnShort.disabled = false;
                currentRoundCandle = null; // Reset for next round
                if (gameStatusEl) {
                    gameStatusEl.innerText = "PLACE YOUR BET";
                    gameStatusEl.className = "game-wait-text";
                }
                currentRoundCandle = null;
            }, 2000);
        }
    }

    function handleWin() {
        if (gameStatusEl) {
            gameStatusEl.innerText = "WIN! +100 CREDITS";
            gameStatusEl.className = "game-win-text";
        }
        gameCredits += 100;
        gameStreak++;
        if (gameScoreEl) gameScoreEl.innerText = gameCredits;

        if (gameCredits >= WINNING_SCORE) {
            triggerWin();
            return;
        }

        if (gameStreak === 3) {
            setTimeout(() => alert("3 WIN STREAK! Keep going!"), 500);
            gameStreak = 0;
        }
    }

    function handleLoss() {
        if (gameStatusEl) {
            gameStatusEl.innerText = "LOSS. -1 LIFE";
            gameStatusEl.className = "game-lose-text";
        }
        gameCredits = Math.max(0, gameCredits - 100);
        gameStreak = 0;
        if (gameScoreEl) gameScoreEl.innerText = gameCredits;

        gameLives--;
        updateLivesDisplay();

        if (gameLives <= 0) {
            triggerGameOver();
        }
    }

    function updateLivesDisplay() {
        let hearts = "";
        for (let i = 0; i < gameLives; i++) hearts += "♥";
        if (gameLivesEl) gameLivesEl.innerText = hearts;
    }

    function triggerWin() {
        gameState = 'GAMEOVER';
        if (endOverlay) {
            endOverlay.style.display = 'flex';
            endOverlay.className = 'game-overlay win';
        }
        if (endTitle) {
            endTitle.innerText = "VICTORY!";
            endTitle.style.color = "#ffd700";
        }
        if (endMsg) {
            endMsg.innerHTML = "FINAL SCORE: " + gameCredits + "<br><br><strong style='color:#0ecb81'>FREE WEEK OF BOUNTY SEEKER!</strong><br>Screenshot this & DM @RickySpanish on Discord";
        }
        if (btnQuit) btnQuit.style.display = 'none';

        // Check monthly play limit
        const lastWinMonth = localStorage.getItem('arcadeWinMonth');
        const currentMonth = new Date().getMonth();
        if (lastWinMonth !== String(currentMonth)) {
            localStorage.setItem('arcadeWinMonth', currentMonth);
        }
    }

    function triggerGameOver() {
        gameState = 'GAMEOVER';
        if (endOverlay) {
            endOverlay.style.display = 'flex';
            endOverlay.className = 'game-overlay lose';
        }
        if (endTitle) {
            endTitle.innerText = "GAME OVER";
            endTitle.style.color = "#ff0055";
        }
        if (endMsg) endMsg.innerText = "FINAL SCORE: " + gameCredits;
        if (btnQuit) btnQuit.style.display = 'none';
    }

    function drawGame() {
        gameCtx.clearRect(0, 0, gameCanvas.width, gameCanvas.height);

        let min = Infinity, max = -Infinity;
        gameCandles.forEach(c => {
            if (c.low < min) min = c.low;
            if (c.high < min) min = c.high;
            if (c.high > max) max = c.high;
        });
        let range = max - min;
        if (range === 0) range = 1;
        const scaleY = (gameCanvas.height - 20) / range;
        const padding = 10;

        // Grid
        gameCtx.strokeStyle = "#222";
        gameCtx.lineWidth = 1;
        gameCtx.beginPath();
        for (let i = 0; i < gameCanvas.width; i += 40) { gameCtx.moveTo(i, 0); gameCtx.lineTo(i, gameCanvas.height); }
        for (let i = 0; i < gameCanvas.height; i += 40) { gameCtx.moveTo(0, i); gameCtx.lineTo(gameCanvas.width, i); }
        gameCtx.stroke();

        // Candles
        gameCandles.forEach((c, i) => {
            let x = i * (CANDLE_WIDTH + CANDLE_SPACING);

            let yOpen = gameCanvas.height - padding - (c.open - min) * scaleY;
            let yClose = gameCanvas.height - padding - (c.close - min) * scaleY;
            let yHigh = gameCanvas.height - padding - (c.high - min) * scaleY;
            let yLow = gameCanvas.height - padding - (c.low - min) * scaleY;

            let isGreen = c.close >= c.open;
            let color = isGreen ? '#0ecb81' : '#ff0055';

            if (gameState === 'RUNNING' && i === gameCandles.length - 1) {
                gameCtx.shadowBlur = 20;
                gameCtx.shadowColor = color;
            } else {
                gameCtx.shadowBlur = 0;
            }

            gameCtx.strokeStyle = color;
            gameCtx.fillStyle = color;

            // Wick
            gameCtx.beginPath();
            gameCtx.moveTo(x + CANDLE_WIDTH / 2, yHigh);
            gameCtx.lineTo(x + CANDLE_WIDTH / 2, yLow);
            gameCtx.stroke();

            // Body
            let bodyH = Math.max(Math.abs(yClose - yOpen), 1);
            let bodyY = Math.min(yOpen, yClose);
            gameCtx.fillRect(x, bodyY, CANDLE_WIDTH, bodyH);
        });

        // Entry Line
        if (gameState === 'RUNNING' && currentRoundCandle) {
            let entryY = gameCanvas.height - padding - (currentRoundCandle.open - min) * scaleY;
            gameCtx.strokeStyle = "#fff";
            gameCtx.setLineDash([5, 5]);
            gameCtx.beginPath();
            gameCtx.moveTo(0, entryY);
            gameCtx.lineTo(gameCanvas.width, entryY);
            gameCtx.stroke();
            gameCtx.setLineDash([]);
        }
    }
})();

// ============================================
// ACTIVE TRADES FUNCTIONALITY
// ============================================
let activeTrades = {};

async function fetchActiveTrades() {
    try {
        const response = await fetch(`active_trades.json?ts=${Date.now()}`);
        if (!response.ok) {
            console.warn('Failed to fetch active trades');
            return;
        }
        const data = await response.json();
        activeTrades = data.active_trades || {};
        renderActiveTrades();
    } catch (error) {
        console.error('Error fetching active trades:', error);
    }
}

function renderActiveTrades() {
    const container = document.getElementById('tradesContainer');
    if (!container) return;

    const trades = Object.entries(activeTrades).filter(([symbol, trade]) => trade.status === 'ACTIVE');

    if (trades.length === 0) {
        container.innerHTML = `
            <div class="trade-empty-state">
                <p>No active trades</p>
            </div>
        `;
        return;
    }

    container.innerHTML = trades.map(([symbol, trade]) => {
        const entryPrice = trade.entry_price || 0;
        const stopLoss = trade.stop_loss || 0;
        const takeProfit = trade.take_profit || 0;

        // Determine if it's a long or short based on entry vs stop loss
        const isLong = takeProfit > entryPrice;
        const direction = isLong ? 'long' : 'short';

        // Calculate current P&L (if we have current price)
        let currentPnL = 0;
        let pnlClass = '';
        if (state.price && state.symbol === symbol.replace('USDT', '')) {
            if (isLong) {
                currentPnL = ((state.price - entryPrice) / entryPrice) * 100;
            } else {
                currentPnL = ((entryPrice - state.price) / entryPrice) * 100;
            }
            pnlClass = currentPnL >= 0 ? 'positive' : 'negative';
        }

        // Calculate risk/reward
        const risk = Math.abs(entryPrice - stopLoss);
        const reward = Math.abs(takeProfit - entryPrice);
        const riskReward = risk > 0 ? (reward / risk).toFixed(2) : '--';

        // Format time
        const signalTime = new Date(trade.signal_time);
        const timeAgo = getTimeAgo(signalTime);

        const priceFormatter = new Intl.NumberFormat('en-US', {
            minimumFractionDigits: trade.entry_price < 1 ? 6 : 2,
            maximumFractionDigits: trade.entry_price < 1 ? 6 : 2
        });

        return `
            <div class="trade-card ${direction}" data-symbol="${symbol}">
                <div class="trade-header">
                    <span class="trade-direction direction-${direction}">${isLong ? 'LONG' : 'SHORT'} ${symbol.replace('USDT', '')}</span>
                    <span class="trade-time">${timeAgo}</span>
                </div>
                <div class="trade-details">
                    <div class="trade-detail">
                        <div class="detail-label">Entry</div>
                        <div class="detail-value">$${priceFormatter.format(entryPrice)}</div>
                    </div>
                    <div class="trade-detail">
                        <div class="detail-label">Target</div>
                        <div class="detail-value">$${priceFormatter.format(takeProfit)}</div>
                    </div>
                    <div class="trade-detail">
                        <div class="detail-label">Stop Loss</div>
                        <div class="detail-value">$${priceFormatter.format(stopLoss)}</div>
                    </div>
                    <div class="trade-detail">
                        <div class="detail-label">Risk/Reward</div>
                        <div class="detail-value">1:${riskReward}</div>
                    </div>
                </div>
                <div class="trade-pnl ${pnlClass}">
                    ${currentPnL !== 0 ? `${currentPnL >= 0 ? '+' : ''}${currentPnL.toFixed(2)}%` : 'Waiting for price data...'}
                </div>
                <div class="trade-actions">
                    <button class="btn-close-trade" onclick="closeActiveTrade('${symbol}')">Close Trade</button>
                </div>
            </div>
        `;
    }).join('');
}

function getTimeAgo(date) {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
}

async function closeActiveTrade(symbol) {
    if (!confirm(`Are you sure you want to close the ${symbol} trade?`)) {
        return;
    }

    try {
        // In a real implementation, this would call a backend API
        // For now, we'll just remove it from the local state and re-render
        if (activeTrades[symbol]) {
            activeTrades[symbol].status = 'CLOSED';
            renderActiveTrades();

            // Optionally send to Discord
            const user = getUsername();
            sendToDiscord({
                username: "Snipers Leaderboard",
                embeds: [{
                    title: `🔻 Trade Closed`,
                    color: 15158332,
                    description: `**${user}** closed **${symbol}** trade`,
                    fields: [
                        { name: "Entry", value: `$${activeTrades[symbol].entry_price}`, inline: true },
                        { name: "Status", value: "CLOSED", inline: true }
                    ],
                    timestamp: new Date().toISOString()
                }]
            });
        }
    } catch (error) {
        console.error('Error closing trade:', error);
        alert('Failed to close trade. Please try again.');
    }
}

// Make closeActiveTrade globally available
window.closeActiveTrade = closeActiveTrade;

// Initialize active trades when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for init() to complete
    setTimeout(() => {
        fetchActiveTrades();
        // Refresh every 30 seconds
        setInterval(fetchActiveTrades, 30000);
    }, 1000);
});

// =========================================
// GPS DASHBOARD FUNCTIONS
// =========================================

let gpsData = {
    currentPrice: 0,
    premiumHigh: 0,
    premiumLow: 0,
    discountHigh: 0,
    discountLow: 0,
    support: 0,
    resistance: 0
};

// Initialize GPS Dashboard
function initGPSDashboard() {
    const selector = document.getElementById('gpsPairSelector');
    const timeframe = document.getElementById('gpsTimeframeSelector');
    const zoneType = document.getElementById('gpsZoneSelector');

    if (selector) {
        selector.addEventListener('change', updateGPSDashboard);
    }
    if (timeframe) {
        timeframe.addEventListener('change', updateGPSDashboard);
    }
    if (zoneType) {
        zoneType.addEventListener('change', updateGPSDashboard);
    }

    // Initial update
    updateGPSDashboard();
}

// Update GPS Dashboard with current data
function updateGPSDashboard() {
    const pair = document.getElementById('gpsPairSelector')?.value || 'BTC';
    const timeframe = document.getElementById('gpsTimeframeSelector')?.value || '4H';
    const zoneType = document.getElementById('gpsZoneSelector')?.value || 'all';

    // Generate mock GPS data based on current price
    const currentPrice = state.price || 95000;

    // Calculate GPS zones (simplified calculation)
    const range = currentPrice * 0.1; // 10% range
    gpsData = {
        currentPrice: currentPrice,
        premiumHigh: currentPrice + (range * 0.7),
        premiumLow: currentPrice + (range * 0.5),
        discountHigh: currentPrice - (range * 0.5),
        discountLow: currentPrice - (range * 0.7),
        support: currentPrice - (range * 0.6),
        resistance: currentPrice + (range * 0.6)
    };

    // Update UI
    updateGPSUI();
}

// Update GPS UI elements
function updateGPSUI() {
    // Update current position
    const positionEl = document.getElementById('gpsCurrentPosition');
    if (positionEl) {
        const position = determineGPSPosition();
        positionEl.textContent = position.text;
        positionEl.style.color = position.color;
    }

    // Update premium zone
    updateGPSZone('premium', gpsData.premiumHigh, gpsData.premiumLow, 'premium');
    updateGPSZone('discount', gpsData.discountHigh, gpsData.discountLow, 'discount');

    // Update support/resistance
    updateSupportResistance('support', gpsData.support);
    updateSupportResistance('resistance', gpsData.resistance);

    // Update last update time
    const updateBadge = document.getElementById('gpsLastUpdate');
    if (updateBadge) {
        updateBadge.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }
}

// Determine current position relative to GPS zones
function determineGPSPosition() {
    const price = gpsData.currentPrice;

    if (price > gpsData.premiumHigh) {
        return { text: 'Above Premium Zone', color: 'var(--neon-purple)' };
    } else if (price > gpsData.premiumLow) {
        return { text: 'In Premium Zone', color: 'var(--neon-purple)' };
    } else if (price > gpsData.discountHigh) {
        return { text: 'Between Zones', color: 'var(--neon-blue)' };
    } else if (price > gpsData.discountLow) {
        return { text: 'In Discount Zone', color: 'var(--neon-green)' };
    } else {
        return { text: 'Below Discount Zone', color: 'var(--neon-purple)' };
    }
}

// Update individual GPS zone
function updateGPSZone(type, high, low, zoneType) {
    const highEl = document.getElementById(`gps${type.charAt(0).toUpperCase() + type.slice(1)}High`);
    const rangeEl = document.getElementById(`gps${type.charAt(0).toUpperCase() + type.slice(1)}Range`);
    const distanceEl = document.getElementById(`gps${type.charAt(0).toUpperCase() + type.slice(1)}Distance`);
    const fillEl = document.getElementById(`gps${type.charAt(0).toUpperCase() + type.slice(1)}Fill`);

    if (highEl) highEl.textContent = `$${high.toFixed(2)}`;
    if (rangeEl) rangeEl.textContent = `$${low.toFixed(2)} to $${high.toFixed(2)}`;

    if (distanceEl) {
        const distance = Math.abs(gpsData.currentPrice - high);
        const percentage = (distance / gpsData.currentPrice * 100).toFixed(2);
        distanceEl.textContent = `${percentage}% away`;
    }

    if (fillEl) {
        // Calculate fill percentage based on current price position
        const totalRange = high - low;
        const currentInZone = Math.max(0, Math.min(totalRange, gpsData.currentPrice - low));
        const fillPercentage = (currentInZone / totalRange * 100);
        fillEl.style.width = `${fillPercentage}%`;
    }
}

// Update support/resistance zones
function updateSupportResistance(type, price) {
    const priceEl = document.getElementById(`gps${type.charAt(0).toUpperCase() + type.slice(1)}Price`);
    const strengthEl = document.getElementById(`gps${type.charAt(0).toUpperCase() + type.slice(1)}Strength`);

    if (priceEl) {
        priceEl.textContent = `$${price.toFixed(2)}`;
    }

    if (strengthEl) {
        // Generate random strength for demo
        const strength = Math.floor(Math.random() * 40) + 60;
        strengthEl.textContent = `${strength}%`;
    }
}

// Refresh GPS data
function refreshGPSData() {
    const btn = document.querySelector('.refresh-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="btn-icon">⏳</span> Loading...';
    }

    // Simulate API call
    setTimeout(() => {
        updateGPSDashboard();

        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-icon">🔄</span> Refresh Data';
        }
    }, 1000);
}

// Make functions globally available
window.updateGPSDashboard = updateGPSDashboard;
window.refreshGPSData = refreshGPSData;

// Initialize GPS dashboard on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initGPSDashboard();
});

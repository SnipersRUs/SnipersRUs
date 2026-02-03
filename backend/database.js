const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
  constructor() {
    this.db = new sqlite3.Database(path.join(__dirname, 'database.sqlite'));
    this.init();
  }

  init() {
    // Signals table
    this.db.run(`
      CREATE TABLE IF NOT EXISTS signals (
        id TEXT PRIMARY KEY,
        provider_address TEXT NOT NULL,
        provider_name TEXT NOT NULL,
        provider_reputation INTEGER DEFAULT 0,
        asset TEXT NOT NULL,
        type TEXT NOT NULL,
        entry REAL NOT NULL,
        target REAL NOT NULL,
        stop_loss REAL NOT NULL,
        timeframe TEXT NOT NULL,
        deadline DATETIME NOT NULL,
        veil_market_id TEXT,
        status TEXT DEFAULT 'ACTIVE',
        outcome TEXT,
        total_volume REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Bets table
    this.db.run(`
      CREATE TABLE IF NOT EXISTS bets (
        id TEXT PRIMARY KEY,
        signal_id TEXT NOT NULL,
        user_address TEXT NOT NULL,
        outcome TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'PENDING',
        veil_order_id TEXT,
        payout REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        settled_at DATETIME,
        FOREIGN KEY (signal_id) REFERENCES signals(id)
      )
    `);

    // Users table
    this.db.run(`
      CREATE TABLE IF NOT EXISTS users (
        address TEXT PRIMARY KEY,
        karma INTEGER DEFAULT 0,
        total_bets INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0,
        profit_loss REAL DEFAULT 0,
        veil_api_key TEXT,
        veil_api_key_expires DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  }

  // Signal methods
  async createSignal(signal) {
    return new Promise((resolve, reject) => {
      const id = `sig_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      this.db.run(
        `INSERT INTO signals (id, provider_address, provider_name, provider_reputation, asset, type, entry, target, stop_loss, timeframe, deadline, veil_market_id)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [id, signal.provider.address, signal.provider.name, signal.provider.reputation, signal.asset, signal.type, signal.entry, signal.target, signal.stopLoss, signal.timeframe, signal.deadline, signal.veilMarketId],
        function(err) {
          if (err) reject(err);
          else resolve({ id, ...signal });
        }
      );
    });
  }

  async getSignals(status = null) {
    return new Promise((resolve, reject) => {
      let query = 'SELECT * FROM signals';
      const params = [];
      
      if (status) {
        query += ' WHERE status = ?';
        params.push(status);
      }
      
      query += ' ORDER BY created_at DESC';
      
      this.db.all(query, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
  }

  async getSignal(id) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM signals WHERE id = ?', [id], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  async updateSignalStatus(id, status, outcome = null) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE signals SET status = ?, outcome = ? WHERE id = ?',
        [status, outcome, id],
        function(err) {
          if (err) reject(err);
          else resolve({ id, status, outcome });
        }
      );
    });
  }

  // Bet methods
  async createBet(bet) {
    return new Promise((resolve, reject) => {
      const id = `bet_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      this.db.run(
        `INSERT INTO bets (id, signal_id, user_address, outcome, amount, veil_order_id)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [id, bet.signalId, bet.userAddress, bet.outcome, bet.amount, bet.veilOrderId],
        function(err) {
          if (err) reject(err);
          else resolve({ id, ...bet });
        }
      );
    });
  }

  async getBetsByUser(address) {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM bets WHERE user_address = ? ORDER BY created_at DESC',
        [address],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows);
        }
      );
    });
  }

  async updateBetStatus(id, status, payout = null) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE bets SET status = ?, payout = ?, settled_at = ? WHERE id = ?',
        [status, payout, new Date().toISOString(), id],
        function(err) {
          if (err) reject(err);
          else resolve({ id, status, payout });
        }
      );
    });
  }

  // User methods
  async getUser(address) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM users WHERE address = ?', [address], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  async createUser(address) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO users (address, karma) VALUES (?, ?)',
        [address, 0],
        function(err) {
          if (err) reject(err);
          else resolve({ address, karma: 0 });
        }
      );
    });
  }

  async updateUserKarma(address, karmaDelta) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE users SET karma = karma + ? WHERE address = ?',
        [karmaDelta, address],
        function(err) {
          if (err) reject(err);
          else resolve({ address, karmaDelta });
        }
      );
    });
  }

  async updateVeilApiKey(address, apiKey, expiresAt) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE users SET veil_api_key = ?, veil_api_key_expires = ? WHERE address = ?',
        [apiKey, expiresAt, address],
        function(err) {
          if (err) reject(err);
          else resolve({ address, apiKey });
        }
      );
    });
  }
}

module.exports = Database;

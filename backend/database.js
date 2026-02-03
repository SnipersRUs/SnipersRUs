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

    // Subscriptions table (for Discord access tiers)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS subscriptions (
        address TEXT PRIMARY KEY,
        tier TEXT NOT NULL,
        tx_hash TEXT,
        start_time DATETIME NOT NULL,
        end_time DATETIME,
        verified_at DATETIME,
        FOREIGN KEY (address) REFERENCES users(address)
      )
    `);

    // Agents table (for autonomous trading agents)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        address TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        capabilities TEXT,
        erc8004_id TEXT,
        reputation INTEGER DEFAULT 100,
        total_signals INTEGER DEFAULT 0,
        win_rate REAL DEFAULT 0,
        total_profit REAL DEFAULT 0,
        verified BOOLEAN DEFAULT FALSE,
        status TEXT DEFAULT 'PENDING',
        reputation_history TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Clawdapedia - Knowledge entries
    this.db.run(`
      CREATE TABLE IF NOT EXISTS knowledge (
        id TEXT PRIMARY KEY,
        contributor TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT NOT NULL,
        tags TEXT,
        sources TEXT,
        quality_score INTEGER DEFAULT 0,
        query_count INTEGER DEFAULT 0,
        earnings INTEGER DEFAULT 0,
        status TEXT DEFAULT 'PENDING',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contributor) REFERENCES agents(address)
      )
    `);

    // Knowledge votes (quality control)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS knowledge_votes (
        entry_id TEXT NOT NULL,
        voter TEXT NOT NULL,
        vote INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (entry_id, voter),
        FOREIGN KEY (entry_id) REFERENCES knowledge(id)
      )
    `);

    // Query tracking (for monetization)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requester TEXT NOT NULL,
        query_text TEXT,
        results_count INTEGER,
        fee INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Contributor earnings
    this.db.run(`
      CREATE TABLE IF NOT EXISTS contributor_earnings (
        address TEXT PRIMARY KEY,
        total_earned INTEGER DEFAULT 0,
        total_withdrawn INTEGER DEFAULT 0,
        pending INTEGER DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Staking pool
    this.db.run(`
      CREATE TABLE IF NOT EXISTS stakes (
        id TEXT PRIMARY KEY,
        address TEXT NOT NULL,
        amount INTEGER NOT NULL,
        staked_at DATETIME NOT NULL,
        rewards_earned INTEGER DEFAULT 0,
        last_claim DATETIME NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        FOREIGN KEY (address) REFERENCES agents(address)
      )
    `);

    // Reward distributions
    this.db.run(`
      CREATE TABLE IF NOT EXISTS reward_distributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT NOT NULL,
        amount INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (address) REFERENCES agents(address)
      )
    `);

    // Sniper Guru Scanner - Staking for access
    this.db.run(`
      CREATE TABLE IF NOT EXISTS scanner_stakes (
        id TEXT PRIMARY KEY,
        address TEXT NOT NULL,
        amount INTEGER NOT NULL,
        staked_at DATETIME NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        fees_paid INTEGER DEFAULT 0,
        unstaked_at DATETIME,
        fee_paid INTEGER,
        returned_amount INTEGER
      )
    `);

    // Dev fees collected
    this.db.run(`
      CREATE TABLE IF NOT EXISTS dev_fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Sniper Guru Signal History
    this.db.run(`
      CREATE TABLE IF NOT EXISTS sniper_guru_signals (
        id TEXT PRIMARY KEY,
        provider TEXT NOT NULL,
        symbol TEXT NOT NULL,
        direction TEXT NOT NULL,
        style TEXT NOT NULL,
        entry REAL NOT NULL,
        stop_loss REAL NOT NULL,
        take_profit REAL NOT NULL,
        confidence INTEGER,
        analysis TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        subscriber TEXT,
        result TEXT,
        profit REAL
      )
    `);

    // Signal requests tracking
    this.db.run(`
      CREATE TABLE IF NOT EXISTS signal_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT NOT NULL,
        symbol TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Scanner usage tracking
    this.db.run(`
      CREATE TABLE IF NOT EXISTS scanner_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT NOT NULL,
        type TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Tip Jar - Tips for Sniper Guru
    this.db.run(`
      CREATE TABLE IF NOT EXISTS tips (
        id TEXT PRIMARY KEY,
        signal_id TEXT NOT NULL,
        tipper TEXT NOT NULL,
        amount INTEGER NOT NULL,
        burn_amount INTEGER NOT NULL,
        guru_amount INTEGER NOT NULL,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'PENDING',
        FOREIGN KEY (signal_id) REFERENCES sniper_guru_signals(id)
      )
    `);

    // Sniper Guru stats (includes tip tracking)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS sniper_guru_stats (
        id INTEGER PRIMARY KEY DEFAULT 1,
        total_tips INTEGER DEFAULT 0,
        total_tipped_amount INTEGER DEFAULT 0,
        total_burned INTEGER DEFAULT 0
      )
    `);

    // Providers table for Signal Wars
    this.db.run(`
      CREATE TABLE IF NOT EXISTS providers (
        address TEXT PRIMARY KEY,
        name TEXT,
        is_agent INTEGER DEFAULT 0,
        karma INTEGER DEFAULT 100,
        win_rate REAL DEFAULT 0,
        total_signals INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Provider fees (for fee claiming)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS provider_fees (
        address TEXT PRIMARY KEY,
        tip_fees INTEGER DEFAULT 0,
        staking_fees INTEGER DEFAULT 0,
        dev_share INTEGER DEFAULT 0,
        last_claim DATETIME,
        FOREIGN KEY (address) REFERENCES providers(address)
      )
    `);

    // Fee claims history
    this.db.run(`
      CREATE TABLE IF NOT EXISTS fee_claims (
        id TEXT PRIMARY KEY,
        address TEXT NOT NULL,
        amount INTEGER NOT NULL,
        tip_fees INTEGER DEFAULT 0,
        staking_fees INTEGER DEFAULT 0,
        dev_share INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'PENDING',
        tx_hash TEXT,
        FOREIGN KEY (address) REFERENCES providers(address)
      )
    `);

    // Burns table (burn-to-earn for dev allocation)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS burns (
        id TEXT PRIMARY KEY,
        address TEXT NOT NULL,
        amount INTEGER NOT NULL,
        allocation_percent INTEGER NOT NULL,
        token_allocation INTEGER NOT NULL,
        burn_tx_hash TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'PENDING',
        used_for_launch INTEGER DEFAULT 0,
        FOREIGN KEY (address) REFERENCES providers(address)
      )
    `);

    // Burn stats
    this.db.run(`
      CREATE TABLE IF NOT EXISTS burn_stats (
        id INTEGER PRIMARY KEY DEFAULT 1,
        total_burned INTEGER DEFAULT 0,
        total_allocations INTEGER DEFAULT 0,
        total_token_supply INTEGER DEFAULT 0
      )
    `);

    // Signal Purchases (pay-per-signal model)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS signal_purchases (
        id TEXT PRIMARY KEY,
        buyer TEXT NOT NULL,
        package TEXT NOT NULL,
        price INTEGER NOT NULL,
        burn_amount INTEGER NOT NULL,
        dev_amount INTEGER NOT NULL,
        tx_hash TEXT,
        signals_remaining INTEGER NOT NULL,
        expires_at DATETIME,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'ACTIVE'
      )
    `);

    // Signal Deliveries (track which signals were delivered to whom)
    this.db.run(`
      CREATE TABLE IF NOT EXISTS signal_deliveries (
        id TEXT PRIMARY KEY,
        purchase_id TEXT NOT NULL,
        buyer TEXT NOT NULL,
        symbol TEXT NOT NULL,
        signal_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (purchase_id) REFERENCES signal_purchases(id)
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

  // Subscription methods
  async getSubscription(address) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM subscriptions WHERE address = ?', [address], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  async upsertSubscription(subscription) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO subscriptions (address, tier, tx_hash, start_time, end_time, verified_at)
         VALUES (?, ?, ?, ?, ?, ?)
         ON CONFLICT(address) DO UPDATE SET
         tier = excluded.tier,
         tx_hash = excluded.tx_hash,
         start_time = excluded.start_time,
         end_time = excluded.end_time,
         verified_at = excluded.verified_at`,
        [subscription.address, subscription.tier, subscription.txHash, subscription.startTime, subscription.endTime, subscription.verifiedAt],
        function(err) {
          if (err) reject(err);
          else resolve(subscription);
        }
      );
    });
  }

  async createSubscription(subscription) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO subscriptions (address, tier, tx_hash, start_time, end_time, verified_at) VALUES (?, ?, ?, ?, ?, ?)',
        [subscription.address, subscription.tier, subscription.txHash, subscription.startTime, subscription.endTime, subscription.verifiedAt],
        function(err) {
          if (err) reject(err);
          else resolve(subscription);
        }
      );
    });
  }

  // Agent methods
  async createAgent(agent) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO agents (id, address, name, description, capabilities, erc8004_id, reputation, total_signals, win_rate, total_profit, verified, status, reputation_history, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [agent.id, agent.address, agent.name, agent.description, JSON.stringify(agent.capabilities), agent.erc8004Id, agent.reputation, agent.totalSignals, agent.winRate, agent.totalProfit, agent.verified, agent.status, JSON.stringify([]), agent.createdAt],
        function(err) {
          if (err) reject(err);
          else resolve(agent);
        }
      );
    });
  }

  async getAgent(address) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM agents WHERE address = ?', [address], (err, row) => {
        if (err) reject(err);
        else {
          if (row && row.capabilities) {
            row.capabilities = JSON.parse(row.capabilities);
          }
          if (row && row.reputation_history) {
            row.reputationHistory = JSON.parse(row.reputation_history);
          }
          resolve(row);
        }
      });
    });
  }

  async getAgentById(id) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM agents WHERE id = ?', [id], (err, row) => {
        if (err) reject(err);
        else {
          if (row && row.capabilities) {
            row.capabilities = JSON.parse(row.capabilities);
          }
          if (row && row.reputation_history) {
            row.reputationHistory = JSON.parse(row.reputation_history);
          }
          resolve(row);
        }
      });
    });
  }

  async getAgents(filters = {}, limit = 20) {
    return new Promise((resolve, reject) => {
      let query = 'SELECT * FROM agents';
      const params = [];
      const conditions = [];

      if (filters.verified) {
        conditions.push('verified = ?');
        params.push(1);
      }
      if (filters.minReputation) {
        conditions.push('reputation >= ?');
        params.push(filters.minReputation);
      }

      if (conditions.length > 0) {
        query += ' WHERE ' + conditions.join(' AND ');
      }

      query += ' ORDER BY reputation DESC LIMIT ?';
      params.push(limit);

      this.db.all(query, params, (err, rows) => {
        if (err) reject(err);
        else {
          rows.forEach(row => {
            if (row.capabilities) row.capabilities = JSON.parse(row.capabilities);
            if (row.reputation_history) row.reputationHistory = JSON.parse(row.reputation_history);
          });
          resolve(rows);
        }
      });
    });
  }

  async updateAgent(id, updates) {
    return new Promise((resolve, reject) => {
      const fields = [];
      const values = [];

      for (const [key, value] of Object.entries(updates)) {
        fields.push(`${key} = ?`);
        values.push(typeof value === 'object' ? JSON.stringify(value) : value);
      }
      values.push(id);

      this.db.run(
        `UPDATE agents SET ${fields.join(', ')} WHERE id = ?`,
        values,
        function(err) {
          if (err) reject(err);
          else resolve({ id, ...updates });
        }
      );
    });
  }

  // Clawdapedia - Knowledge methods
  async createKnowledgeEntry(entry) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO knowledge (id, contributor, title, content, category, tags, sources, quality_score, query_count, earnings, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [entry.id, entry.contributor, entry.title, entry.content, entry.category, JSON.stringify(entry.tags), JSON.stringify(entry.sources), entry.qualityScore, entry.queryCount, entry.earnings, entry.status, entry.createdAt, entry.updatedAt],
        function(err) {
          if (err) reject(err);
          else resolve(entry);
        }
      );
    });
  }

  async getKnowledgeEntry(id) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM knowledge WHERE id = ?', [id], (err, row) => {
        if (err) reject(err);
        else {
          if (row) {
            row.tags = JSON.parse(row.tags || '[]');
            row.sources = JSON.parse(row.sources || '[]');
          }
          resolve(row);
        }
      });
    });
  }

  async searchKnowledge({ query, category, tags, minQuality = 0, limit = 10 }) {
    return new Promise((resolve, reject) => {
      let sql = 'SELECT * FROM knowledge WHERE quality_score >= ? AND status IN ("ACTIVE", "GOLD")';
      const params = [minQuality];

      if (category) {
        sql += ' AND category = ?';
        params.push(category);
      }

      if (tags && tags.length > 0) {
        sql += ' AND (' + tags.map(() => 'tags LIKE ?').join(' OR ') + ')';
        tags.forEach(tag => params.push(`%${tag}%`));
      }

      if (query) {
        sql += ' AND (title LIKE ? OR content LIKE ?)';
        params.push(`%${query}%`, `%${query}%`);
      }

      sql += ' ORDER BY quality_score DESC, query_count DESC LIMIT ?';
      params.push(limit);

      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else {
          rows.forEach(row => {
            row.tags = JSON.parse(row.tags || '[]');
            row.sources = JSON.parse(row.sources || '[]');
          });
          resolve(rows);
        }
      });
    });
  }

  async updateKnowledgeQuality(id, qualityScore) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE knowledge SET quality_score = ?, updated_at = ? WHERE id = ?',
        [qualityScore, new Date().toISOString(), id],
        function(err) {
          if (err) reject(err);
          else resolve({ id, qualityScore });
        }
      );
    });
  }

  async updateKnowledgeStatus(id, status) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE knowledge SET status = ?, updated_at = ? WHERE id = ?',
        [status, new Date().toISOString(), id],
        function(err) {
          if (err) reject(err);
          else resolve({ id, status });
        }
      );
    });
  }

  async incrementQueryCount(id) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE knowledge SET query_count = query_count + 1 WHERE id = ?',
        [id],
        function(err) {
          if (err) reject(err);
          else resolve({ id });
        }
      );
    });
  }

  async incrementKnowledgeEarnings(id, amount) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE knowledge SET earnings = earnings + ? WHERE id = ?',
        [amount, id],
        function(err) {
          if (err) reject(err);
          else resolve({ id, amount });
        }
      );
    });
  }

  async recordVote(entryId, voter, vote) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO knowledge_votes (entry_id, voter, vote) VALUES (?, ?, ?)',
        [entryId, voter, vote],
        function(err) {
          if (err) reject(err);
          else resolve({ entryId, voter, vote });
        }
      );
    });
  }

  async getVote(entryId, voter) {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM knowledge_votes WHERE entry_id = ? AND voter = ?',
        [entryId, voter],
        (err, row) => {
          if (err) reject(err);
          else resolve(row);
        }
      );
    });
  }

  async getDailyQueries(requester) {
    return new Promise((resolve, reject) => {
      const today = new Date().toISOString().split('T')[0];
      this.db.get(
        'SELECT COUNT(*) as count FROM queries WHERE requester = ? AND DATE(created_at) = ?',
        [requester, today],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.count : 0);
        }
      );
    });
  }

  async getMonthlyQueries(requester) {
    return new Promise((resolve, reject) => {
      const now = new Date();
      const firstDay = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
      this.db.get(
        'SELECT COUNT(*) as count FROM queries WHERE requester = ? AND created_at >= ?',
        [requester, firstDay],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.count : 0);
        }
      );
    });
  }

  async recordQuery(requester, queryText, resultsCount, fee) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO queries (requester, query_text, results_count, fee) VALUES (?, ?, ?, ?)',
        [requester, queryText, resultsCount, fee],
        function(err) {
          if (err) reject(err);
          else resolve({ id: this.lastID });
        }
      );
    });
  }

  // Signal Provider Platform methods
  async createSignal(signal) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO signals (id, provider, type, symbol, entry, stop_loss, take_profit, timeframe, reasoning, is_agent, status, karma_at_submit, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [signal.id, signal.provider, signal.type, signal.symbol, signal.entry, signal.stopLoss, signal.takeProfit, signal.timeframe, signal.reasoning, signal.isAgent, signal.status, signal.karmaAtSubmit, signal.createdAt],
        function(err) {
          if (err) reject(err);
          else resolve(signal);
        }
      );
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

  async getSignals({ mode, status, limit = 20, offset = 0 }) {
    return new Promise((resolve, reject) => {
      let sql = 'SELECT * FROM signals WHERE status = ?';
      const params = [status];

      if (mode === 'agent') {
        sql += ' AND is_agent = 1';
      } else if (mode === 'human') {
        sql += ' AND is_agent = 0';
      }

      sql += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
      params.push(limit, offset);

      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows || []);
      });
    });
  }

  async updateSignalResult(id, result) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE signals SET result = ?, result_price = ?, result_time = ?, status = ? WHERE id = ?',
        [result.result, result.resultPrice, result.resultTime, result.status, id],
        function(err) {
          if (err) reject(err);
          else resolve({ id, ...result });
        }
      );
    });
  }

  async getProvider(address) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM providers WHERE address = ?', [address], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  async updateProviderKarma(address, delta) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE providers SET karma = karma + ? WHERE address = ?',
        [delta, address],
        function(err) {
          if (err) reject(err);
          else resolve({ address, delta });
        }
      );
    });
  }

  async updateProvider(address, updates) {
    return new Promise((resolve, reject) => {
      const fields = [];
      const values = [];

      for (const [key, value] of Object.entries(updates)) {
        fields.push(`${key} = ?`);
        values.push(value);
      }
      values.push(address);

      this.db.run(
        `UPDATE providers SET ${fields.join(', ')} WHERE address = ?`,
        values,
        function(err) {
          if (err) reject(err);
          else resolve({ address, ...updates });
        }
      );
    });
  }

  async getProviderSignals(address, limit = 10) {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM signals WHERE provider = ? ORDER BY created_at DESC LIMIT ?',
        [address, limit],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  async getTopProviders({ isAgent, limit = 10 }) {
    return new Promise((resolve, reject) => {
      let sql = 'SELECT * FROM providers';
      const params = [];

      if (isAgent !== null) {
        sql += ' WHERE is_agent = ?';
        params.push(isAgent ? 1 : 0);
      }

      sql += ' ORDER BY karma DESC, win_rate DESC LIMIT ?';
      params.push(limit);

      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows || []);
      });
    });
  }

  async getTeamStats(isAgent) {
    return new Promise((resolve, reject) => {
      this.db.get(
        `SELECT 
          COUNT(*) as totalSignals,
          AVG(win_rate) as winRate,
          AVG(karma) as avgKarma
         FROM providers 
         WHERE is_agent = ? AND total_signals > 0`,
        [isAgent ? 1 : 0],
        (err, row) => {
          if (err) reject(err);
          else resolve(row || { totalSignals: 0, winRate: 0, avgKarma: 0 });
        }
      );
    });
  }

  async recordQueryPayment(requester, fee) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO queries (requester, fee) VALUES (?, ?)',
        [requester, fee],
        function(err) {
          if (err) reject(err);
          else resolve({ requester, fee });
        }
      );
    });
  }

  async updateContributorEarnings(address, amount) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO contributor_earnings (address, total_earned, pending) VALUES (?, ?, ?)
         ON CONFLICT(address) DO UPDATE SET
         total_earned = total_earned + ?,
         pending = pending + ?,
         updated_at = ?`,
        [address, amount, amount, amount, amount, new Date().toISOString()],
        function(err) {
          if (err) reject(err);
          else resolve({ address, amount });
        }
      );
    });
  }

  async getContributorEarnings(address) {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT pending FROM contributor_earnings WHERE address = ?',
        [address],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.pending : 0);
        }
      );
    });
  }

  async resetContributorEarnings(address) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `UPDATE contributor_earnings 
         SET total_withdrawn = total_withdrawn + pending,
             pending = 0,
             updated_at = ?
         WHERE address = ?`,
        [new Date().toISOString(), address],
        function(err) {
          if (err) reject(err);
          else resolve({ address });
        }
      );
    });
  }

  async getContributorKnowledge(address) {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM knowledge WHERE contributor = ? ORDER BY created_at DESC',
        [address],
        (err, rows) => {
          if (err) reject(err);
          else {
            rows.forEach(row => {
              row.tags = JSON.parse(row.tags || '[]');
            });
            resolve(rows);
          }
        }
      );
    });
  }

  async getKnowledgeByCategory(category, sort = 'quality', limit = 20) {
    return new Promise((resolve, reject) => {
      let orderBy = 'quality_score DESC';
      if (sort === 'popular') orderBy = 'query_count DESC';
      if (sort === 'newest') orderBy = 'created_at DESC';

      this.db.all(
        `SELECT * FROM knowledge WHERE category = ? AND status IN ("ACTIVE", "GOLD") 
         ORDER BY ${orderBy} LIMIT ?`,
        [category, limit],
        (err, rows) => {
          if (err) reject(err);
          else {
            rows.forEach(row => {
              row.tags = JSON.parse(row.tags || '[]');
            });
            resolve(rows);
          }
        }
      );
    });
  }

  // Staking methods
  async createStake(stake) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO stakes (id, address, amount, staked_at, rewards_earned, last_claim, status)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [stake.id, stake.address, stake.amount, stake.stakedAt, stake.rewardsEarned, stake.lastClaim, stake.status],
        function(err) {
          if (err) reject(err);
          else resolve(stake);
        }
      );
    });
  }

  async getActiveStake(address) {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM stakes WHERE address = ? AND status = "ACTIVE"',
        [address],
        (err, row) => {
          if (err) reject(err);
          else resolve(row);
        }
      );
    });
  }

  async updateStakeStatus(id, status) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE stakes SET status = ? WHERE id = ?',
        [status, id],
        function(err) {
          if (err) reject(err);
          else resolve({ id, status });
        }
      );
    });
  }

  async updateStakeRewards(address, amount) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE stakes SET rewards_earned = rewards_earned + ?, last_claim = ? WHERE address = ? AND status = "ACTIVE"',
        [amount, new Date().toISOString(), address],
        function(err) {
          if (err) reject(err);
          else resolve({ address, amount });
        }
      );
    });
  }

  async getTotalStaked() {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT COALESCE(SUM(amount), 0) as total FROM stakes WHERE status = "ACTIVE"',
        [],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.total : 0);
        }
      );
    });
  }

  async updateTotalStaked(delta) {
    // This is handled automatically by SUM in getTotalStaked
    return Promise.resolve();
  }

  async getStakerCount() {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT COUNT(*) as count FROM stakes WHERE status = "ACTIVE"',
        [],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.count : 0);
        }
      );
    });
  }

  async getTotalRewardsDistributed() {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT COALESCE(SUM(amount), 0) as total FROM reward_distributions',
        [],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.total : 0);
        }
      );
    });
  }

  async getPlatformFeesSince(timestamp) {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT COALESCE(SUM(fee), 0) as total FROM queries WHERE created_at > ?',
        [timestamp],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.total : 0);
        }
      );
    });
  }

  async getPlatformFeesLastDays(days) {
    return new Promise((resolve, reject) => {
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - days);
      
      this.db.get(
        'SELECT COALESCE(SUM(fee), 0) as total FROM queries WHERE created_at > ?',
        [cutoff.toISOString()],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.total : 0);
        }
      );
    });
  }

  async recordRewardDistribution(address, amount) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO reward_distributions (address, amount, created_at) VALUES (?, ?, ?)',
        [address, amount, new Date().toISOString()],
        function(err) {
          if (err) reject(err);
          else resolve({ address, amount });
        }
      );
    });
  }

  async getTopStakers(limit = 10) {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT s.*, ROUND(s.amount * 100.0 / (SELECT COALESCE(SUM(amount), 1) FROM stakes WHERE status = "ACTIVE"), 2) as sharePercent 
         FROM stakes s 
         WHERE s.status = "ACTIVE" 
         ORDER BY s.amount DESC 
         LIMIT ?`,
        [limit],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  // Sniper Guru Scanner methods
  async createScannerStake(stake) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO scanner_stakes (id, address, amount, staked_at, status, fees_paid)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [stake.id, stake.address, stake.amount, stake.stakedAt, stake.status, stake.feesPaid],
        function(err) {
          if (err) reject(err);
          else resolve(stake);
        }
      );
    });
  }

  async getScannerStake(address) {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM scanner_stakes WHERE address = ? AND status = "ACTIVE"',
        [address],
        (err, row) => {
          if (err) reject(err);
          else resolve(row);
        }
      );
    });
  }

  async updateScannerStake(id, updates) {
    return new Promise((resolve, reject) => {
      const fields = [];
      const values = [];

      for (const [key, value] of Object.entries(updates)) {
        fields.push(`${key} = ?`);
        values.push(value);
      }
      values.push(id);

      this.db.run(
        `UPDATE scanner_stakes SET ${fields.join(', ')} WHERE id = ?`,
        values,
        function(err) {
          if (err) reject(err);
          else resolve({ id, ...updates });
        }
      );
    });
  }

  async recordDevFee(amount) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO dev_fees (amount, created_at) VALUES (?, ?)',
        [amount, new Date().toISOString()],
        function(err) {
          if (err) reject(err);
          else resolve({ amount });
        }
      );
    });
  }

  async createSniperGuruSignal(signal) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO sniper_guru_signals (id, provider, symbol, direction, style, entry, stop_loss, take_profit, confidence, analysis, timestamp, subscriber)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [signal.id, signal.provider, signal.symbol, signal.direction, signal.style, signal.entry, signal.stopLoss, signal.takeProfit, signal.confidence, JSON.stringify(signal.analysis), signal.timestamp, signal.subscriber],
        function(err) {
          if (err) reject(err);
          else resolve(signal);
        }
      );
    });
  }

  async getSniperGuruSignals({ subscriber, limit = 50, offset = 0 }) {
    return new Promise((resolve, reject) => {
      let sql = 'SELECT * FROM sniper_guru_signals';
      const params = [];

      if (subscriber) {
        sql += ' WHERE subscriber = ?';
        params.push(subscriber);
      }

      sql += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?';
      params.push(limit, offset);

      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else {
          rows.forEach(row => {
            if (row.analysis) row.analysis = JSON.parse(row.analysis);
          });
          resolve(rows || []);
        }
      });
    });
  }

  async getSniperGuruStats(subscriber) {
    return new Promise((resolve, reject) => {
      this.db.get(
        `SELECT 
          COUNT(*) as total,
          AVG(CASE WHEN result = 'HIT' THEN 1 ELSE 0 END) * 100 as winRate,
          AVG(profit) as avgProfit
         FROM sniper_guru_signals 
         WHERE subscriber = ? AND result IS NOT NULL`,
        [subscriber],
        (err, row) => {
          if (err) reject(err);
          else resolve(row || { total: 0, winRate: 0, avgProfit: 0 });
        }
      );
    });
  }

  async getTodaySignalCount(address) {
    return new Promise((resolve, reject) => {
      const today = new Date().toISOString().split('T')[0];
      this.db.get(
        'SELECT COUNT(*) as count FROM sniper_guru_signals WHERE subscriber = ? AND DATE(timestamp) = ?',
        [address, today],
        (err, row) => {
          if (err) reject(err);
          else resolve(row ? row.count : 0);
        }
      );
    });
  }

  async recordSignalRequest(address, symbol) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO signal_requests (address, symbol, created_at) VALUES (?, ?, ?)',
        [address, symbol, new Date().toISOString()],
        function(err) {
          if (err) reject(err);
          else resolve({ address, symbol });
        }
      );
    });
  }

  async recordScannerUsage(address, type) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO scanner_usage (address, type, created_at) VALUES (?, ?, ?)',
        [address, type, new Date().toISOString()],
        function(err) {
          if (err) reject(err);
          else resolve({ address, type });
        }
      );
    });
  }

  // Tip Jar methods
  async createTip(tip) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO tips (id, signal_id, tipper, amount, burn_amount, guru_amount, message, timestamp, status)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [tip.id, tip.signalId, tip.tipper, tip.amount, tip.burnAmount, tip.guruAmount, tip.message, tip.timestamp, tip.status],
        function(err) {
          if (err) reject(err);
          else resolve(tip);
        }
      );
    });
  }

  async incrementSignalTips(signalId, amount) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE sniper_guru_signals SET tips_received = COALESCE(tips_received, 0) + ? WHERE id = ?',
        [amount, signalId],
        function(err) {
          if (err) reject(err);
          else resolve({ signalId, amount });
        }
      );
    });
  }

  async updateSniperGuruTips(guruAmount, burnAmount) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO sniper_guru_stats (id, total_tips, total_tipped_amount, total_burned)
         VALUES (1, 1, ?, ?)
         ON CONFLICT(id) DO UPDATE SET
         total_tips = total_tips + 1,
         total_tipped_amount = total_tipped_amount + ?,
         total_burned = total_burned + ?`,
        [guruAmount, burnAmount, guruAmount, burnAmount],
        function(err) {
          if (err) reject(err);
          else resolve({ guruAmount, burnAmount });
        }
      );
    });
  }

  async getSniperGuruTipStats() {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM sniper_guru_stats WHERE id = 1',
        [],
        (err, row) => {
          if (err) reject(err);
          else {
            const stats = row || { total_tips: 0, total_tipped_amount: 0, total_burned: 0 };
            
            // Get top tippers
            this.db.all(
              `SELECT tipper, SUM(amount) as total FROM tips 
               GROUP BY tipper 
               ORDER BY total DESC 
               LIMIT 10`,
              [],
              (err2, tippers) => {
                if (err2) reject(err2);
                else {
                  resolve({
                    totalTips: stats.total_tips || 0,
                    totalAmount: stats.total_tipped_amount || 0,
                    totalBurned: stats.total_burned || 0,
                    totalToGuru: (stats.total_tipped_amount || 0) - (stats.total_burned || 0),
                    topTippers: tippers || []
                  });
                }
              }
            );
          }
        }
      );
    });
  }

  async getTipsForSignal(signalId) {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM tips WHERE signal_id = ? ORDER BY timestamp DESC',
        [signalId],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  // Tipper leaderboard
  async getTipperLeaderboard(limit = 20) {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT 
          tipper as address,
          SUM(amount) as total,
          COUNT(*) as count,
          MAX(timestamp) as lastTip
         FROM tips 
         GROUP BY tipper 
         ORDER BY total DESC 
         LIMIT ?`,
        [limit],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  // Signal Provider Platform methods
  async createSignal(signal) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO signals (id, provider_address, asset, type, entry, target, stop_loss, timeframe, status, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [signal.id, signal.provider, signal.symbol, signal.type, signal.entry, signal.takeProfit, signal.stopLoss, signal.timeframe, signal.status, signal.createdAt.toISOString()],
        function(err) {
          if (err) reject(err);
          else resolve(signal);
        }
      );
    });
  }

  async getSignal(id) {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM signals WHERE id = ?',
        [id],
        (err, row) => {
          if (err) reject(err);
          else resolve(row);
        }
      );
    });
  }

  async updateSignalResult(id, updates) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE signals SET outcome = ?, status = ? WHERE id = ?',
        [updates.result, updates.status, id],
        function(err) {
          if (err) reject(err);
          else resolve({ id, ...updates });
        }
      );
    });
  }

  async getSignals({ mode, status, limit, offset }) {
    return new Promise((resolve, reject) => {
      let sql = 'SELECT * FROM signals WHERE 1=1';
      const params = [];

      if (status) {
        sql += ' AND status = ?';
        params.push(status);
      }

      sql += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
      params.push(limit, offset);

      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows || []);
      });
    });
  }

  async getProvider(address) {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM providers WHERE address = ?',
        [address],
        (err, row) => {
          if (err) reject(err);
          else resolve(row);
        }
      );
    });
  }

  async createProvider(provider) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO providers (address, name, is_agent, karma, win_rate, total_signals, wins, losses)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [provider.address, provider.name, provider.isAgent ? 1 : 0, provider.karma || 100, provider.winRate || 0, provider.totalSignals || 0, provider.wins || 0, provider.losses || 0],
        function(err) {
          if (err) reject(err);
          else resolve(provider);
        }
      );
    });
  }

  async updateProvider(address, updates) {
    return new Promise((resolve, reject) => {
      const fields = [];
      const values = [];

      for (const [key, value] of Object.entries(updates)) {
        fields.push(`${key} = ?`);
        values.push(value);
      }
      values.push(address);

      this.db.run(
        `UPDATE providers SET ${fields.join(', ')} WHERE address = ?`,
        values,
        function(err) {
          if (err) reject(err);
          else resolve({ address, ...updates });
        }
      );
    });
  }

  async updateProviderKarma(address, delta) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'UPDATE providers SET karma = karma + ? WHERE address = ?',
        [delta, address],
        function(err) {
          if (err) reject(err);
          else resolve({ address, delta });
        }
      );
    });
  }

  async getTopProviders({ isAgent, limit }) {
    return new Promise((resolve, reject) => {
      let sql = 'SELECT * FROM providers WHERE 1=1';
      const params = [];

      if (isAgent !== null && isAgent !== undefined) {
        sql += ' AND is_agent = ?';
        params.push(isAgent ? 1 : 0);
      }

      sql += ' ORDER BY karma DESC LIMIT ?';
      params.push(limit);

      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows || []);
      });
    });
  }

  async getTeamStats(isAgent) {
    return new Promise((resolve, reject) => {
      this.db.get(
        `SELECT 
          COUNT(*) as totalSignals,
          AVG(win_rate) as winRate,
          AVG(karma) as avgKarma
         FROM providers 
         WHERE is_agent = ?`,
        [isAgent ? 1 : 0],
        (err, row) => {
          if (err) reject(err);
          else resolve(row || { totalSignals: 0, winRate: 0, avgKarma: 0 });
        }
      );
    });
  }

  async getProviderSignals(address, limit) {
    return new Promise((resolve, reject) => {
      this.db.all(
        'SELECT * FROM signals WHERE provider_address = ? ORDER BY created_at DESC LIMIT ?',
        [address, limit],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  // Get single Sniper Guru signal (for tip tracking)
  async getSniperGuruSignal(id) {
    return new Promise((resolve, reject) => {
      this.db.get(
        'SELECT * FROM sniper_guru_signals WHERE id = ?',
        [id],
        (err, row) => {
          if (err) reject(err);
          else resolve(row);
        }
      );
    });
  }

  // Fee claiming methods
  async getProviderFees(address) {
    return new Promise((resolve, reject) => {
      this.db.get(
        `SELECT * FROM provider_fees WHERE address = ?`,
        [address],
        (err, row) => {
          if (err) reject(err);
          else resolve(row || { tipFees: 0, stakingFees: 0, devShare: 0, lastClaim: null });
        }
      );
    });
  }

  async resetProviderFees(address) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO provider_fees (address, tip_fees, staking_fees, dev_share, last_claim)
         VALUES (?, 0, 0, 0, ?)
         ON CONFLICT(address) DO UPDATE SET
         tip_fees = 0,
         staking_fees = 0,
         dev_share = 0,
         last_claim = ?`,
        [address, new Date().toISOString(), new Date().toISOString()],
        function(err) {
          if (err) reject(err);
          else resolve({ address });
        }
      );
    });
  }

  async createFeeClaim(claim) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO fee_claims (id, address, amount, tip_fees, staking_fees, dev_share, timestamp, status)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [claim.id, claim.address, claim.amount, claim.breakdown.tips, claim.breakdown.staking, claim.breakdown.devShare, claim.timestamp.toISOString(), claim.status],
        function(err) {
          if (err) reject(err);
          else resolve(claim);
        }
      );
    });
  }

  async getFeeClaimHistory(address, limit = 20) {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT * FROM fee_claims WHERE address = ? ORDER BY timestamp DESC LIMIT ?`,
        [address, limit],
        (err, rows) => {
          if (err) reject(err);
          else {
            rows.forEach(row => {
              row.breakdown = {
                tips: row.tip_fees,
                staking: row.staking_fees,
                devShare: row.dev_share
              };
            });
            resolve(rows || []);
          }
        }
      );
    });
  }

  // Burn methods (burn-to-earn)
  async createBurn(burn) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO burns (id, address, amount, allocation_percent, token_allocation, burn_tx_hash, timestamp, status, used_for_launch)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [burn.id, burn.address, burn.amount, burn.allocationPercent, burn.tokenAllocation, burn.burnTxHash, burn.timestamp.toISOString(), burn.status, burn.usedForLaunch ? 1 : 0],
        function(err) {
          if (err) reject(err);
          else resolve(burn);
        }
      );
    });
  }

  async updateBurnStats(amount, tokenAllocation) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO burn_stats (id, total_burned, total_allocations, total_token_supply)
         VALUES (1, ?, ?, ?)
         ON CONFLICT(id) DO UPDATE SET
         total_burned = total_burned + ?,
         total_allocations = total_allocations + 1,
         total_token_supply = total_token_supply + ?`,
        [amount, 1, tokenAllocation, amount, tokenAllocation],
        function(err) {
          if (err) reject(err);
          else resolve({ amount, tokenAllocation });
        }
      );
    });
  }

  async getBurnStats() {
    return new Promise((resolve, reject) => {
      this.db.get(
        `SELECT * FROM burn_stats WHERE id = 1`,
        [],
        (err, row) => {
          if (err) reject(err);
          else resolve(row || { totalBurned: 0, totalAllocations: 0, totalTokenSupply: 0 });
        }
      );
    });
  }

  async getBurnsByAddress(address) {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT * FROM burns WHERE address = ? ORDER BY timestamp DESC`,
        [address],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  // Signal Purchase methods (simple pay-per-signal)
  async createSignalPurchase(purchase) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO signal_purchases (id, buyer, package, price, burn_amount, dev_amount, tx_hash, signals_remaining, expires_at, timestamp, status)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [purchase.id, purchase.buyer, purchase.package, purchase.price, purchase.burnAmount, purchase.devAmount, purchase.txHash, purchase.signalsRemaining, purchase.expiresAt?.toISOString(), purchase.timestamp.toISOString(), purchase.status],
        function(err) {
          if (err) reject(err);
          else resolve(purchase);
        }
      );
    });
  }

  async getActivePurchases(address) {
    return new Promise((resolve, reject) => {
      const now = new Date().toISOString();
      this.db.all(
        `SELECT * FROM signal_purchases 
         WHERE buyer = ? 
         AND status = 'ACTIVE' 
         AND (expires_at IS NULL OR expires_at > ?)
         AND signals_remaining > 0
         ORDER BY timestamp ASC`,
        [address, now],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }

  async useSignalCredit(purchaseId) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `UPDATE signal_purchases SET signals_remaining = signals_remaining - 1 WHERE id = ?`,
        [purchaseId],
        function(err) {
          if (err) reject(err);
          else resolve({ id: purchaseId });
        }
      );
    });
  }

  async recordSignalDelivery(delivery) {
    return new Promise((resolve, reject) => {
      this.db.run(
        `INSERT INTO signal_deliveries (id, purchase_id, buyer, symbol, signal_id, timestamp)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [delivery.id, delivery.purchaseId, delivery.buyer, delivery.symbol, delivery.signalId, delivery.timestamp.toISOString()],
        function(err) {
          if (err) reject(err);
          else resolve(delivery);
        }
      );
    });
  }

  async getPublicSignals({ limit, offset }) {
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT * FROM sniper_guru_signals ORDER BY timestamp DESC LIMIT ? OFFSET ?`,
        [limit, offset],
        (err, rows) => {
          if (err) reject(err);
          else resolve(rows || []);
        }
      );
    });
  }
}

module.exports = Database;

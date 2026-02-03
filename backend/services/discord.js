// Discord webhook service for transaction notifications
const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL || 'https://discord.com/api/webhooks/1462820633632051386/hhIkkWGp1y6uBZO7y225mwk2GNiRSliZqgNdb5cgMkonDSCodhlwcAJhilZ-aIKdE6QT';

class DiscordService {
  constructor() {
    this.webhookUrl = DISCORD_WEBHOOK_URL;
  }

  async sendTransactionNotification(type, data) {
    try {
      const embed = this.createTransactionEmbed(type, data);
      
      const response = await fetch(this.webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          embeds: [embed],
        }),
      });

      if (!response.ok) {
        console.error('Discord webhook failed:', await response.text());
      }
    } catch (err) {
      console.error('Discord notification error:', err);
    }
  }

  createTransactionEmbed(type, data) {
    const colors = {
      stake: 0x00ff00,      // Green
      unstake: 0xff0000,    // Red
      tip: 0xffd700,        // Gold
      burn: 0xff6600,       // Orange
      signal: 0x00ffff,     // Cyan
    };

    const titles = {
      stake: '💰 CLAWNCH Staked',
      unstake: '💸 CLAWNCH Unstaked',
      tip: '💎 ZOID Tip Received',
      burn: '🔥 ZOID Burned',
      signal: '🎯 Signal Posted',
    };

    const embed = {
      title: titles[type] || 'Transaction',
      color: colors[type] || 0xffffff,
      timestamp: new Date().toISOString(),
      fields: [
        {
          name: 'Wallet',
          value: `\`${data.address?.slice(0, 6)}...${data.address?.slice(-4)}\``,
          inline: true,
        },
      ],
      footer: {
        text: 'SnipersRUs Transaction Monitor',
      },
    };

    // Add type-specific fields
    switch (type) {
      case 'stake':
        embed.fields.push(
          { name: 'Amount', value: `${data.amount} CLAWNCH`, inline: true },
          { name: 'Tier', value: data.tier || 'BASIC', inline: true },
          { name: 'Tx Hash', value: data.txHash ? `[View](https://basescan.org/tx/${data.txHash})` : 'Pending', inline: false }
        );
        break;

      case 'unstake':
        embed.fields.push(
          { name: 'Original Stake', value: `${data.originalStake} CLAWNCH`, inline: true },
          { name: 'Fee (5%)', value: `${data.fee} CLAWNCH`, inline: true },
          { name: 'Returned', value: `${data.returnAmount} CLAWNCH`, inline: true }
        );
        break;

      case 'tip':
        embed.fields.push(
          { name: 'Amount', value: `${data.amount} ZOID`, inline: true },
          { name: 'To Sniper Guru', value: `${data.guruAmount} ZOID (75%)`, inline: true },
          { name: 'Burned', value: `${data.burnAmount} ZOID (25%)`, inline: true }
        );
        if (data.message) {
          embed.description = `💬 *"${data.message}"*`;
        }
        break;

      case 'burn':
        embed.fields.push(
          { name: 'Amount Burned', value: `${data.amount} ZOID`, inline: true },
          { name: 'Dev Allocation', value: `${data.allocationPercent}%`, inline: true },
          { name: 'Token Supply', value: `${data.tokenAllocation?.toLocaleString()} tokens`, inline: true }
        );
        break;

      case 'signal':
        embed.fields.push(
          { name: 'Symbol', value: data.symbol, inline: true },
          { name: 'Direction', value: data.direction, inline: true },
          { name: 'Provider Type', value: data.isAgent ? '🤖 Agent' : '👤 Human', inline: true },
          { name: 'Entry', value: `$${data.entry}`, inline: true },
          { name: 'Target', value: `$${data.takeProfit}`, inline: true },
          { name: 'Stop Loss', value: `$${data.stopLoss}`, inline: true }
        );
        break;
    }

    return embed;
  }

  async sendStakeNotification(address, amount, tier, txHash) {
    return this.sendTransactionNotification('stake', { address, amount, tier, txHash });
  }

  async sendUnstakeNotification(address, originalStake, fee, returnAmount) {
    return this.sendTransactionNotification('unstake', { address, originalStake, fee, returnAmount });
  }

  async sendTipNotification(tipper, amount, guruAmount, burnAmount, message, signalId) {
    return this.sendTransactionNotification('tip', { address: tipper, amount, guruAmount, burnAmount, message, signalId });
  }

  async sendBurnNotification(address, amount, allocationPercent, tokenAllocation) {
    return this.sendTransactionNotification('burn', { address, amount, allocationPercent, tokenAllocation });
  }

  async sendSignalNotification(provider, symbol, direction, entry, takeProfit, stopLoss, isAgent) {
    return this.sendTransactionNotification('signal', { address: provider, symbol, direction, entry, takeProfit, stopLoss, isAgent });
  }
}

module.exports = DiscordService;

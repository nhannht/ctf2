

import crypto from 'node:crypto';
import { VAULT_KEY } from './config.js';
import { verifyJWT } from './crypto-helpers.js';

const AUDIT_LOG = [
  { at: "2026-04-12T08:21:03Z", actor: "admin", action: "vault_unlock", success: false },
  { at: "2026-04-12T08:21:18Z", actor: "admin", action: "vault_unlock", success: true  },
  { at: "2026-04-29T17:55:41Z", actor: "admin", action: "key_rotate",   success: true  },
  { at: "2026-05-01T03:02:09Z", actor: "admin", action: "vault_unlock", success: true  },
];
const AUDIT_LOG_MAX = 200;

function recordAudit(entry) {
  AUDIT_LOG.push(entry);
  if (AUDIT_LOG.length > AUDIT_LOG_MAX) AUDIT_LOG.splice(0, AUDIT_LOG.length - AUDIT_LOG_MAX);
}

export class UserApi {
  static openVaults(token, key) {
    return new this(token).openVault(key);
  }

  static audit(token) {
    return new this(token).getAuditLog();
  }

  static whoAmI(token) {
    return new this(token).me();
  }

  constructor(token) {
    this.session = verifyJWT(token);
  }

  openVault(key) {
    if (!this.session?.isAdmin) throw new Error("admin access required");
    const success = key == this.getVaultSecret();
    recordAudit({
      at: new Date().toISOString(),
      actor: this.session.sub ?? 'unknown',
      action: 'vault_unlock',
      success,
    });
    if (success) {
      return {
        success: true,
        message:
          "Vault cracked! Transfer of $6,767,676,767 initiated. " +
          `Your cheque code is ${this.getVaultSecret()}. (You may want to leave the country.)`,
        receipt_id: "TXN-" + crypto.randomBytes(4).toString('hex').toUpperCase(),
      };
    }
    return { success: false, message: "wrong key" };
  }

  getAuditLog() {
    if (!this.session?.isAdmin) throw new Error("admin access required");
    return { entries: AUDIT_LOG.slice(-50) };
  }

  me() {
    return this.session;
  }

  getVaultSecret() {
    return VAULT_KEY;
  }
}

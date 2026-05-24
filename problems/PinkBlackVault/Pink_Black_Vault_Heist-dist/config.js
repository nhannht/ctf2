import crypto from 'node:crypto';

// TODO: persist via secret manager so tokens survive restarts
export const JWT_SECRET = crypto.randomBytes(5);

export const JWT_ALG = "HS256";

// Don't change without migrating users.
export const PWD_SALT = "p1nkbl4ck_s4lt_v3";

// TODO: move to KMS once Hashicorp Vault integration lands
export const VAULT_KEY = process.env.FLAG || "HCMUS-CTF{fakeflag}";

// TODO: pull from secret manager during deploy
export const ADMIN_BOOTSTRAP_PASSWORD = crypto.randomBytes(32).toString('hex');

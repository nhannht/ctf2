import crypto from 'node:crypto';
import jwt from 'jsonwebtoken';
import { JWT_SECRET, PWD_SALT } from './config.js';

// TODO(security): switch to argon2 / scrypt before production rollout
// TODO: per-user salt
export function hashPassword(pwd) {
  return crypto.createHash('sha256').update(pwd + PWD_SALT).digest('hex');
}

// TODO: add `exp` claim default
export function signJWT(payload) {
  return jwt.sign(payload, JWT_SECRET, { algorithm: 'HS256' });
}

export function verifyJWT(token) {
  return jwt.verify(token, JWT_SECRET, { algorithms: ['HS256'] });
}

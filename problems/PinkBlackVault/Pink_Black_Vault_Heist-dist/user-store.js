import { ADMIN_BOOTSTRAP_PASSWORD } from './config.js';
import { hashPassword, signJWT } from './crypto-helpers.js';

export const flag = new Map();

flag.set("admin", {
  password_hash: hashPassword(ADMIN_BOOTSTRAP_PASSWORD),
  isAdmin: true,
});

const USERNAME_MIN = 3;
const USERNAME_MAX = 32;

export function registerUser(username, password) {
  if (typeof username !== 'string' || typeof password !== 'string') {
    throw new Error("username and password are required");
  }
  if (username.length < USERNAME_MIN || username.length > USERNAME_MAX) {
    throw new Error(`username must be ${USERNAME_MIN}-${USERNAME_MAX} characters`);
  }
  if (flag.has(username)) {
    throw new Error("username already taken");
  }
  flag.set(username, {
    password_hash: hashPassword(password),
    isAdmin: false,
  });
  return { ok: true, username };
}

export function loginUser(username, password) {
  const user = flag.get(username);
  if (!user || user.password_hash !== hashPassword(password)) {
    throw new Error("invalid credentials");
  }
  return {
    token: signJWT({ sub: username, isAdmin: user.isAdmin }),
    isAdmin: user.isAdmin,
  };
}

export function countUsers() {
  return flag.size;
}

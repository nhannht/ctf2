import { registerUser, loginUser, countUsers } from './user-store.js';

export class AuthApi {
  static register(username, password) { return registerUser(username, password); }
  static login(username, password)    { return loginUser(username, password); }
  static userCount()                  { return countUsers(); }
}

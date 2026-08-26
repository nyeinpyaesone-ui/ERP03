"use strict";

import { openDB } from "idb";
import { AsyncStorageError } from "../AsyncStorageError.js";
const WebStorageTableName = "entries";
/**
 * Registry to keep one IndexedDB connection per database name.
 */
class IndexedDBConnectionRegistry {
  registry = new Map();
  TableName = WebStorageTableName;
  getOrCreate(dbName) {
    if (this.registry.has(dbName)) {
      return this.registry.get(dbName);
    }
    const db = openDB(dbName, 1, {
      upgrade: db => {
        if (!db.objectStoreNames.contains(WebStorageTableName)) {
          db.createObjectStore(WebStorageTableName);
        }
      },
      blocked: (currentVersion, blockedVersion, _) => {
        throw AsyncStorageError.jsError(`New version (${blockedVersion}) is blocked by current one (${currentVersion})`, AsyncStorageError.Type.WebStorageError);
      },
      blocking: (currentVersion, blockedVersion, _) => {
        throw AsyncStorageError.jsError(`Current db version (${currentVersion}) is blocking upgrade to next version (${blockedVersion})`, AsyncStorageError.Type.WebStorageError);
      }
    });
    this.registry.set(dbName, db);

    // in case of error while opening, clear the storage to retry
    db.catch(err => {
      this.registry.delete(dbName);
      throw err;
    });
    return db;
  }
}
export default new IndexedDBConnectionRegistry();
//# sourceMappingURL=IndexedDBConnectionRegistry.js.map
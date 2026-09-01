"use strict";

import { AsyncStorageError } from "./AsyncStorageError.js";
import IndexedDBStorage from "./web-module/IndexedDBStorage.js";

/**
 * Creates a new AsyncStorage instance bound to a given database name.
 * @param databaseName - The name of the database to open or create.
 */
export function createAsyncStorage(databaseName) {
  return new AsyncStorageWebImpl(databaseName);
}

/**
 * AsyncStorage implementation for web using IndexedDB.
 * Each instance operates on its own IndexedDB database.
 */
class AsyncStorageWebImpl {
  constructor(dbName) {
    this.db = new IndexedDBStorage(dbName);
  }
  getItem = async key => {
    try {
      const result = await this.db.getValues([key]);
      const value = result?.[0] ?? null;
      return value?.value ?? null;
    } catch (e) {
      throw this.createError(e);
    }
  };
  setItem = async (key, value) => {
    try {
      await this.db.setValues([{
        key,
        value
      }]);
    } catch (e) {
      throw this.createError(e);
    }
  };
  removeItem = async key => {
    try {
      await this.db.removeValues([key]);
    } catch (e) {
      throw this.createError(e);
    }
  };
  getMany = async keys => {
    try {
      return await this.db.getValues(keys).then(entries => entries.reduce((values, current) => {
        values[current.key] = current.value;
        return values;
      }, {}));
    } catch (e) {
      throw this.createError(e);
    }
  };
  setMany = async entries => {
    try {
      await this.db.setValues(Object.entries(entries).map(([key, value]) => ({
        key,
        value
      })));
    } catch (e) {
      throw this.createError(e);
    }
  };
  removeMany = async keys => {
    try {
      await this.db.removeValues(keys);
    } catch (e) {
      throw this.createError(e);
    }
  };
  getAllKeys = async () => {
    try {
      return await this.db.getKeys();
    } catch (e) {
      throw this.createError(e);
    }
  };
  clear = async () => {
    try {
      await this.db.clearStorage();
    } catch (e) {
      throw this.createError(e);
    }
  };
  createError(e) {
    if (e instanceof AsyncStorageError) {
      return e;
    }
    return AsyncStorageError.jsError(e?.message ?? `Web storage error: ${e}`, AsyncStorageError.Type.WebStorageError);
  }
}

/**
 * Returns a singleton instance of the legacy (v2) web AsyncStorage implementation.
 *
 * ⚠️ Usage is discouraged. This is provided only as a migration path to v3.
 */
export function getLegacyStorage() {
  return LegacyAsyncStorageWebImpl.instance;
}

/**
 * Legacy AsyncStorage implementation, backed by LocalStorage Web API.
 * Singleton to ensure consistent state across calls.
 */
class LegacyAsyncStorageWebImpl {
  constructor() {}
  static instance = new LegacyAsyncStorageWebImpl();
  get storage() {
    return window.localStorage;
  }
  getItem = async key => {
    return this.storage.getItem(key) ?? null;
  };
  setItem = async (key, value) => {
    this.storage.setItem(key, value);
  };
  removeItem = async key => {
    this.storage.removeItem(key);
  };
  getMany = async keys => {
    return keys.reduce((entries, current) => {
      entries[current] = this.storage.getItem(current) ?? null;
      return entries;
    }, {});
  };
  setMany = async entries => {
    Object.entries(entries).forEach(([key, value]) => {
      this.storage.setItem(key, value);
    });
  };
  removeMany = async keys => {
    keys.forEach(key => {
      this.storage.removeItem(key);
    });
  };
  getAllKeys = async () => {
    return Object.keys(this.storage);
  };
  clear = async () => {
    this.storage.clear();
  };
}
//# sourceMappingURL=createAsyncStorage.js.map
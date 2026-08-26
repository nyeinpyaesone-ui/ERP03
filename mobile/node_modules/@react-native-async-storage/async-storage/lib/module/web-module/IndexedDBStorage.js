"use strict";

import { AsyncStorageError } from "../AsyncStorageError.js";
import registry from "./IndexedDBConnectionRegistry.js";
class IndexedDBStorage {
  constructor(dbName) {
    this.dbName = dbName;
  }
  getValues = async keys => {
    try {
      const db = await this.db();
      const tx = db.transaction(registry.TableName, "readonly");
      const store = tx.objectStore(registry.TableName);
      const result = await Promise.all(keys.map(async key => {
        const entry = await store.get(key);
        return {
          key,
          value: entry ?? null
        };
      }));
      await tx.done;
      return result;
    } catch (e) {
      throw this.createError(e);
    }
  };
  setValues = async values => {
    try {
      const db = await this.db();
      const tx = db.transaction(registry.TableName, "readwrite");
      const store = tx.objectStore(registry.TableName);
      const result = await Promise.all(values.map(async entry => {
        await store.put(entry.value, entry.key);
        return {
          key: entry.key,
          value: entry.value
        };
      }));
      await tx.done;
      return result;
    } catch (e) {
      throw this.createError(e);
    }
  };
  removeValues = async keys => {
    try {
      const db = await this.db();
      const tx = db.transaction(registry.TableName, "readwrite");
      const store = tx.objectStore(registry.TableName);
      await Promise.all(keys.map(async key => {
        await store.delete(key);
      }));
    } catch (e) {
      throw this.createError(e);
    }
  };
  clearStorage = async () => {
    try {
      const db = await this.db();
      await db.clear(registry.TableName);
    } catch (e) {
      throw this.createError(e);
    }
  };
  getKeys = async () => {
    try {
      const db = await this.db();
      return await db.getAllKeys(registry.TableName);
    } catch (e) {
      throw this.createError(e);
    }
  };
  db = () => registry.getOrCreate(this.dbName);
  createError(e) {
    if (e instanceof AsyncStorageError) {
      return e;
    }
    return AsyncStorageError.jsError(e?.message ?? `IndexedDB error: ${e}`, AsyncStorageError.Type.WebStorageError);
  }
}
export default IndexedDBStorage;
//# sourceMappingURL=IndexedDBStorage.js.map
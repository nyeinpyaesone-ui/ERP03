"use strict";

class AsyncStorageMemoryImpl {
  store = new Map();
  getItem = async key => {
    return this.store.get(key) ?? null;
  };
  setItem = async (key, value) => {
    this.store.set(key, value);
  };
  removeItem = async key => {
    this.store.delete(key);
  };
  getMany = async keys => {
    return keys.reduce((result, key) => {
      result[key] = this.store.get(key) ?? null;
      return result;
    }, {});
  };
  setMany = async entries => {
    for (const [key, value] of Object.entries(entries)) {
      this.store.set(key, value);
    }
  };
  removeMany = async keys => {
    for (const key of keys) {
      this.store.delete(key);
    }
  };
  getAllKeys = async () => {
    return Array.from(this.store.keys());
  };
  clear = async () => {
    this.store.clear();
  };
}
const inMemoryDbRegistry = new Map();
export function createAsyncStorage(databaseName) {
  if (!inMemoryDbRegistry.has(databaseName)) {
    inMemoryDbRegistry.set(databaseName, new AsyncStorageMemoryImpl());
  }
  return inMemoryDbRegistry.get(databaseName);
}
export function clearAllMockStorages() {
  inMemoryDbRegistry.clear();
}
export default createAsyncStorage("legacy");
//# sourceMappingURL=AsyncStorageMock.js.map
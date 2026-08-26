"use strict";

import { AsyncStorageError } from "./AsyncStorageError.js";
import { TurboModuleRegistry } from "react-native";

/**
 * Due to Windows native target not being supported by Room KMP,
 * custom storages are not available. Instead, this module falls back
 * to the legacy v2 AsyncStorage implementation.
 */
let warned = false;

/**
 * Creates an AsyncStorage instance.
 * On Windows, always falls back to legacy storage.
 */
export function createAsyncStorage(_) {
  if (!warned && __DEV__) {
    warned = true;
    // eslint-disable-next-line
    console.warn("[AsyncStorage] Warning: Creating custom storages is not supported on Windows. Falling back to the legacy implementation.");
  }
  return getLegacyStorage();
}

/** Returns a singleton instance of the legacy (v2) AsyncStorage implementation. */
export function getLegacyStorage() {
  return LegacyAsyncStorageImpl.instance;
}
class LegacyAsyncStorageImpl {
  constructor() {}
  static instance = new LegacyAsyncStorageImpl();
  get db() {
    const mod = RNCAsyncStorage;
    if (!mod) {
      throw AsyncStorageError.jsError(`Native module is null, cannot access storage.`, AsyncStorageError.Type.NativeModuleError);
    }
    return mod;
  }
  getItem = async key => {
    try {
      return await new Promise((resolve, reject) => {
        this.db.multiGet([key], (errors, result) => {
          const error = this.getError(errors);
          if (error) {
            return reject(error);
          }
          resolve(result?.[0]?.[1] ?? null);
        });
      });
    } catch (e) {
      throw AsyncStorageError.nativeError(e);
    }
  };
  setItem = async (key, value) => {
    try {
      await new Promise((resolve, reject) => {
        this.db.multiSet([[key, value]], errors => {
          const error = this.getError(errors);
          if (error) {
            return reject(error);
          }
          resolve();
        });
      });
    } catch (e) {
      throw AsyncStorageError.nativeError(e);
    }
  };
  removeItem = async key => {
    try {
      await new Promise((resolve, reject) => {
        this.db.multiRemove([key], errors => {
          const error = this.getError(errors);
          if (error) {
            return reject(error);
          }
          resolve();
        });
      });
    } catch (e) {
      throw AsyncStorageError.nativeError(e);
    }
  };
  getMany = async keys => {
    try {
      return await new Promise((resolve, reject) => {
        this.db.multiGet(keys, (errors, result) => {
          const error = this.getError(errors);
          if (error) {
            return reject(error);
          }
          const resultMap = new Map(result);
          const entries = {};
          for (const key of keys) {
            entries[key] = resultMap.get(key) ?? null;
          }
          resolve(entries);
        });
      });
    } catch (e) {
      throw AsyncStorageError.nativeError(e);
    }
  };
  setMany = async entries => {
    try {
      await new Promise((resolve, reject) => {
        this.db.multiSet(Object.entries(entries), errors => {
          const error = this.getError(errors);
          if (error) {
            return reject(error);
          }
          resolve();
        });
      });
    } catch (e) {
      throw AsyncStorageError.nativeError(e);
    }
  };
  removeMany = async keys => {
    try {
      await new Promise((resolve, reject) => {
        this.db.multiRemove(keys, errors => {
          const error = this.getError(errors);
          if (error) {
            return reject(error);
          }
          resolve();
        });
      });
    } catch (e) {
      throw AsyncStorageError.nativeError(e);
    }
  };
  getAllKeys = async () => {
    try {
      return await new Promise((resolve, reject) => {
        this.db.getAllKeys((errors, result) => {
          const error = this.getError(errors);
          if (error) {
            return reject(error);
          }
          if (!result) {
            return reject(AsyncStorageError.jsError("Invalid state, no error and no values returned", AsyncStorageError.Type.UnknownError));
          }
          resolve(result);
        });
      });
    } catch (e) {
      throw AsyncStorageError.nativeError(e);
    }
  };
  clear = async () => {
    try {
      await new Promise((resolve, reject) => {
        this.db.clear(errors => {
          const error = this.getError(errors);
          if (error) {
            return reject(error);
          }
          resolve();
        });
      });
    } catch (e) {
      throw AsyncStorageError.nativeError(e);
    }
  };
  getError = potentialError => {
    if (!potentialError) {
      return null;
    }
    if (Array.isArray(potentialError) && potentialError.length) {
      const firstError = potentialError.find(e => e?.message);
      if (firstError) {
        return firstError;
      }
      return null;
    } else if (potentialError?.message) {
      return potentialError;
    }
    return null;
  };
}

/**
 * Backward compatibility layer to support the Windows target in v3.
 * Room KMP does not currently support the Windows native target,
 * so shared-storage cannot be used on Windows.
 * See: https://issuetracker.google.com/issues/363195546
 */
const RNCAsyncStorage = TurboModuleRegistry.get("RNCAsyncStorage");
//# sourceMappingURL=createAsyncStorage.windows.js.map
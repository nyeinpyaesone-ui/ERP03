/**
 * Asynchronous key-value storage interface compatible with the Web Storage API.
 */
export interface AsyncStorage {
  /**
   * Retrieves a single item from storage.
   * @param key - The key identifying the stored value.
   * @returns A Promise resolving to the stored string value,
   *          or `null` if the key does not exist.
   * @throws {@link AsyncStorageError}
   */
  getItem(key: string): Promise<string | null>;

  /**
   * Stores or updates an item in storage.
   * @param key - The key under which the value will be stored.
   * @param value - The string value to store.
   * @returns A Promise that resolves once the value has been written.
   * @throws {@link AsyncStorageError} if writing fails.
   */
  setItem(key: string, value: string): Promise<void>;

  /**
   * Removes an item from storage.
   * @param key - The key of the item to remove.
   * @returns A Promise that resolves once the key has been removed.
   * @throws {@link AsyncStorageError} if removal fails.
   */
  removeItem(key: string): Promise<void>;

  /**
   * Retrieves multiple items from storage.
   * @param keys - An array of keys to retrieve.
   * @returns A Promise resolving to an object mapping each key to its stored value,
   *          or `null` for keys that do not exist.
   * @throws {@link AsyncStorageError} if retrieval fails.
   */
  getMany(keys: string[]): Promise<Record<string, string | null>>;

  /**
   * Stores multiple items in storage.
   * @param entries - An object containing key-value pairs to store.
   * @returns A Promise that resolves once all items have been written.
   * @throws {@link AsyncStorageError} if writing fails.
   */
  setMany(entries: Record<string, string>): Promise<void>;

  /**
   * Removes multiple items from storage.
   * @param keys - An array of keys to remove.
   * @returns A Promise that resolves once all keys have been removed.
   * @throws {@link AsyncStorageError} if removal fails.
   */
  removeMany(keys: string[]): Promise<void>;

  /**
   * Retrieves all keys currently stored.
   * @returns A Promise resolving to an array of keys.
   * @throws {@link AsyncStorageError} if retrieval fails.
   */
  getAllKeys(): Promise<string[]>;

  /**
   * Clears all data from the storage.
   * @returns A Promise that resolves once the storage has been cleared.
   * @throws {@link AsyncStorageError} if clearing fails.
   */
  clear(): Promise<void>;
}

package org.asyncstorage

import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReadableArray
import com.facebook.react.module.annotations.ReactModule
import org.asyncstorage.legacy_storage.LegacyStorageModule
import org.asyncstorage.storage.StorageRegistry

@ReactModule(name = AsyncStorageModule.NAME)
class AsyncStorageModule(private val reactContext: ReactApplicationContext) :
    NativeAsyncStorageSpec(reactContext) {

    private val legacyStorage = LegacyStorageModule(reactContext)

    override fun getName() = NAME

    override fun getValues(db: String, keys: ReadableArray, promise: Promise) {
        StorageRegistry.getRNStorage(reactContext, db).run { get(keys, promise) }
    }

    override fun setValues(db: String, values: ReadableArray, promise: Promise) {
        StorageRegistry.getRNStorage(reactContext, db).run { set(values, promise) }
    }

    override fun removeValues(db: String, keys: ReadableArray, promise: Promise) {
        StorageRegistry.getRNStorage(reactContext, db).run { remove(keys, promise) }
    }

    override fun getKeys(db: String, promise: Promise) {
        StorageRegistry.getRNStorage(reactContext, db).run { allKeys(promise) }
    }

    override fun clearStorage(db: String, promise: Promise) {
        StorageRegistry.getRNStorage(reactContext, db).run { clear(promise) }
    }

    override fun legacy_multiGet(keys: ReadableArray, promise: Promise) {
        legacyStorage.multiGet(keys, promise)
    }

    override fun legacy_multiSet(kvPairs: ReadableArray, promise: Promise) {
        legacyStorage.multiSet(kvPairs, promise)
    }

    override fun legacy_getAllKeys(promise: Promise) {
        legacyStorage.getAllKeys(promise)
    }

    override fun legacy_multiRemove(keys: ReadableArray, promise: Promise) {
        legacyStorage.multiRemove(keys, promise)
    }

    override fun legacy_multiMerge(kvPairs: ReadableArray, promise: Promise) {
        legacyStorage.multiMerge(kvPairs, promise)
    }

    override fun legacy_clear(promise: Promise) {
        legacyStorage.clear(promise)
    }

    companion object {
        const val NAME = "RNAsyncStorage"
    }
}

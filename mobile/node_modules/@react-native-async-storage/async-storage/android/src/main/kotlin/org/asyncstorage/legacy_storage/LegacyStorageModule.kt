package org.asyncstorage.legacy_storage

import android.content.Context
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReadableArray
import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class LegacyStorageModule(reactContext: ReactApplicationContext) : CoroutineScope {

    override val coroutineContext =
        Dispatchers.IO + CoroutineName("AsyncStorageScope") + SupervisorJob()

    private val storage = StorageSupplier.getInstance(reactContext)

    companion object {
        @JvmStatic
        fun getStorageInstance(ctx: Context): AsyncStorageAccess {
            return StorageSupplier.getInstance(ctx)
        }
    }

    fun multiGet(keys: ReadableArray, promise: Promise) {
        launch(createExceptionHandler(promise)) {
            val entries = storage.getValues(keys.toKeyList())
            promise.resolve(entries.toKeyValueArgument())
        }
    }

    fun multiSet(keyValueArray: ReadableArray, promise: Promise) {
        launch(createExceptionHandler(promise)) {
            val entries = keyValueArray.toEntryList()
            storage.setValues(entries)
            promise.resolve(null)
        }
    }

    fun multiRemove(keys: ReadableArray, promise: Promise) {
        launch(createExceptionHandler(promise)) {
            storage.removeValues(keys.toKeyList())
            promise.resolve(null)
        }
    }

    fun multiMerge(keyValueArray: ReadableArray, promise: Promise) {
        launch(createExceptionHandler(promise)) {
            val entries = keyValueArray.toEntryList()
            storage.mergeValues(entries)
            promise.resolve(null)
        }
    }

    fun getAllKeys(promise: Promise) {
        launch(createExceptionHandler(promise)) {
            val keys = storage.getKeys()
            val result = Arguments.createArray()
            keys.forEach { result.pushString(it) }
            promise.resolve(result)
        }
    }

    fun clear(promise: Promise) {
        launch(createExceptionHandler(promise)) {
            storage.clear()
            promise.resolve(null)
        }
    }
}

internal fun createExceptionHandler(promise: Promise): CoroutineExceptionHandler {
    return CoroutineExceptionHandler { _, throwable ->
        val error = Arguments.createMap()
        error.putString("type", "LegacyStorageException")
        error.putString(
            "message",
            throwable.message
                ?: throwable.localizedMessage
                ?: "Unknown LegacyAsyncStorage error: $throwable",
        )

        promise.reject(code = "AsyncStorageError", throwable, userInfo = error)
    }
}

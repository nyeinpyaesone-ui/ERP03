package org.asyncstorage.storage

import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReadableArray
import com.facebook.react.bridge.WritableMap
import kotlin.coroutines.CoroutineContext
import kotlin.coroutines.EmptyCoroutineContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.plus
import org.asyncstorage.shared_storage.SharedStorage
import org.asyncstorage.shared_storage.StorageException

private val createStorageScope = { name: String ->
    CoroutineScope(SupervisorJob() + CoroutineName(name))
}

class RNStorage(
    private val db: SharedStorage,
    dbName: String,
    coroutineContext: CoroutineContext = EmptyCoroutineContext,
) {
    private val scope = createStorageScope(dbName) + coroutineContext

    fun get(rnKeys: ReadableArray, promise: Promise) =
        scope.lunchWithRejection(promise) {
            val keys = rnKeys.toKeyList()
            val result = db.getValues(keys).toRNResults()
            promise.resolve(result)
        }

    fun set(values: ReadableArray, promise: Promise) =
        scope.lunchWithRejection(promise) {
            val entries = values.toEntryList()
            val result = db.setValues(entries).toRNResults()
            promise.resolve(result)
        }

    fun remove(keys: ReadableArray, promise: Promise) =
        scope.lunchWithRejection(promise) {
            db.removeValues(keys.toKeyList())
            promise.resolve(null)
        }

    fun allKeys(promise: Promise) =
        scope.lunchWithRejection(promise) {
            val result = db.getKeys().toRNKeys()
            promise.resolve(result)
        }

    fun clear(promise: Promise) =
        scope.lunchWithRejection(promise) {
            db.clear()
            promise.resolve(null)
        }
}

private fun <T> CoroutineScope.lunchWithRejection(promise: Promise, block: suspend () -> T) {
    launch {
        try {
            block()
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {

            var userInfo: WritableMap? = null

            if (e is StorageException) {
                userInfo =
                    Arguments.createMap().also {
                        if (e is StorageException.SqliteException) {
                            it.putString("type", "SqliteException")
                        } else {
                            it.putString("type", "OtherException")
                        }
                    }
            }

            promise.reject(
                code = "AsyncStorageError",
                message = e.message,
                throwable = e,
                userInfo = userInfo,
            )
        }
    }
}

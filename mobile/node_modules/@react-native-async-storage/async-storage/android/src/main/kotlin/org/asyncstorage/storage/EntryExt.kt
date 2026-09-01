package org.asyncstorage.storage

import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.ReadableArray
import com.facebook.react.bridge.ReadableMap
import org.asyncstorage.shared_storage.Entry

/**
 * From Shared Entry to RN Entry.
 *
 * js expects: { key: string; value: string | null }
 */
internal fun Entry.toRNResult(): ReadableMap =
    Arguments.createMap().apply {
        putString("key", key)
        putString("value", value)
    }

/**
 * From Shared Entry list to RN Entry list.
 *
 * js expects: { key: string; value: string | null }
 */
internal fun List<Entry>.toRNResults(): ReadableArray {
    val list = Arguments.createArray()
    for (entry in this) {
        list.pushMap(entry.toRNResult())
    }
    return list
}

private fun ReadableMap.toEntry(): Entry {
    val key = getString("key") ?: error("Missing key in map from RN")
    val value = getString("value")
    return Entry(key, value)
}

internal fun ReadableArray.toEntryList(): List<Entry> {
    val list = mutableListOf<Entry>()

    for (i in 0..<size()) {
        val rnEntry = getMap(i)
        requireNotNull(rnEntry)
        list.add(rnEntry.toEntry())
    }

    return list
}

internal fun ReadableArray.toKeyList(): List<String> = toArrayList().map { it.toString() }

internal fun List<String>.toRNKeys(): ReadableArray {
    val list = Arguments.createArray()
    for (key in this) {
        list.pushString(key)
    }
    return list
}

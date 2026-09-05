"use strict";

var AsyncStorageErrorType = /*#__PURE__*/function (AsyncStorageErrorType) {
  /**
   * Related to RN Native module itself, ex. not initialized or null at app boot
   */
  AsyncStorageErrorType["NativeModuleError"] = "NativeModuleError";
  /**
   * Related to web storage (indexedDB)
   * https://developer.mozilla.org/en-US/docs/Web/API/IDBRequest/error
   */
  AsyncStorageErrorType["WebStorageError"] = "WebStorageError";
  /**
   * Error thrown from Sqlite itself
   * https://www.sqlite.org/rescode.html
   */
  AsyncStorageErrorType["SqliteStorageError"] = "SqliteStorageError";
  /**
   * Other errors related to Native Shared Storage or Legacy Storage exception.
   * ex. Storage could not be initialized or wrongly formatted output is generated
   */
  AsyncStorageErrorType["OtherStorageError"] = "OtherStorageError";
  /**
   * Catch-all case, where we can't really tell what went wrong
   */
  AsyncStorageErrorType["UnknownError"] = "UnknownError";
  return AsyncStorageErrorType;
}(AsyncStorageErrorType || {});
export class AsyncStorageError extends Error {
  constructor(errorMessage, type) {
    super(errorMessage);
    this.errorMessage = errorMessage;
    this.type = type;
    this.name = this.constructor.name;
  }
  static nativeError(e) {
    // do not override own error
    if (e instanceof AsyncStorageError) {
      throw e;
    }
    const error = getNativeError(e);
    if (!error) {
      return new AsyncStorageError(e?.message ?? `Unknown error ${e}`, AsyncStorageErrorType.UnknownError);
    }
    let errorType = AsyncStorageErrorType.UnknownError;
    switch (error.type) {
      case "SqliteException":
        errorType = AsyncStorageErrorType.SqliteStorageError;
        break;
      case "OtherException":
        errorType = AsyncStorageErrorType.OtherStorageError;
        break;
    }
    return new AsyncStorageError(error.message, errorType);
  }
  static jsError(error, type) {
    return new AsyncStorageError(error, type);
  }
  static Type = AsyncStorageErrorType;
}

// Native module reject promises with special code
function isNativeError(e) {
  if (typeof e !== "object") {
    return false;
  }
  const err = e;
  return !!err.message && err?.code === "AsyncStorageError";
}
function getNativeError(e) {
  if (!isNativeError(e)) {
    return null;
  }
  const errorType = e.userInfo ? e.userInfo["type"] : null;
  switch (errorType) {
    case "SqliteException":
      {
        return {
          type: "SqliteException",
          message: e.message
        };
      }
    case "OtherException":
      {
        return {
          type: "OtherException",
          message: e.message
        };
      }
    case "LegacyStorageException":
      {
        return {
          type: "LegacyStorageException",
          message: e.message
        };
      }
  }
  return null;
}
//# sourceMappingURL=AsyncStorageError.js.map
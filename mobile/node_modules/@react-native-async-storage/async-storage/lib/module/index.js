"use strict";

import { getLegacyStorage } from "./createAsyncStorage";
export { createAsyncStorage } from "./createAsyncStorage";
export { AsyncStorageError } from "./AsyncStorageError.js";

// Legacy storage that is proxy to an old storage data.
export default getLegacyStorage();
//# sourceMappingURL=index.js.map
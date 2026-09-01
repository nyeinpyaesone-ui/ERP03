/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

#import <Foundation/Foundation.h>

#import <React/RCTBridgeModule.h>
#import <React/RCTInvalidating.h>

/**
 * A simple, asynchronous, persistent, key-value storage system designed as a
 * backend to the AsyncStorage JS module, which is modeled after LocalStorage.
 *
 * Current implementation stores small values in serialized dictionary and
 * larger values in separate files. Since we use a serial file queue
 * `RKFileQueue`, reading/writing from multiple threads should be perceived as
 * being atomic, unless someone bypasses the `RNCAsyncStorage` API.
 *
 * Keys and values must always be strings or an error is returned.
 */

NS_ASSUME_NONNULL_BEGIN

@interface RNCAsyncStorage : NSObject <RCTInvalidating>

@property (nonatomic, assign) BOOL clearOnInvalidate;

@property (nonatomic, readonly, getter=isValid) BOOL valid;

+ (instancetype)sharedInstance;

- (dispatch_queue_t)methodQueue;

// Clear the RNCAsyncStorage data from native code
- (void)clearAllData;

// For clearing data when the bridge may not exist, e.g. when logging out.
+ (void)clearAllData;

- (nullable NSDictionary<NSString *, NSString *> *)multiGet:(NSArray<NSString *> *)keys
                                                      error:(NSError **)error;

- (BOOL)multiSet:(NSArray<NSArray<NSString *> *> *)kvPairs error:(NSError **)error;

- (BOOL)multiRemove:(NSArray<NSString *> *)keys error:(NSError **)error;

- (nullable NSArray<NSString *> *)getAllKeys:(NSError **)error;

- (BOOL)clear:(NSError **)error;

@end

NS_ASSUME_NONNULL_END

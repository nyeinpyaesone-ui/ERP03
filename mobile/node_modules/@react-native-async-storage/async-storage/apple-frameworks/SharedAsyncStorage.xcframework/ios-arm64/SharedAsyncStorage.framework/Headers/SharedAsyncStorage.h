#import <Foundation/NSArray.h>
#import <Foundation/NSDictionary.h>
#import <Foundation/NSError.h>
#import <Foundation/NSObject.h>
#import <Foundation/NSSet.h>
#import <Foundation/NSString.h>
#import <Foundation/NSValue.h>

@class SAS__SkieSuspendWrappersKt, SASUShort, SASULong, SASUInt, SASUByte, SASStorageExceptionSqliteException, SASStorageExceptionOtherException, SASStorageException, SASStorageDatabase_Impl, SASStorageDatabaseConstructor, SASStorageDatabaseCompanion, SASStorageDatabase, SASSkie_SuspendResultSuccess, SASSkie_SuspendResultError, SASSkie_SuspendResultCanceled, SASSkie_SuspendResult, SASSkie_SuspendHandler, SASSkie_CancellationHandler, SASSkieKotlinStateFlow<T>, SASSkieKotlinSharedFlow<T>, SASSkieKotlinOptionalStateFlow<T>, SASSkieKotlinOptionalSharedFlow<T>, SASSkieKotlinOptionalMutableStateFlow<T>, SASSkieKotlinOptionalMutableSharedFlow<T>, SASSkieKotlinOptionalFlow<T>, SASSkieKotlinMutableStateFlow<T>, SASSkieKotlinMutableSharedFlow<T>, SASSkieKotlinFlow<T>, SASSkieColdFlowIterator<E>, SASShort, SASSharedStorage_appleKt, SASRoom_runtimeRoomOpenDelegateValidationResult, SASRoom_runtimeRoomOpenDelegate, SASRoom_runtimeRoomDatabase, SASRoom_runtimeMigration, SASRoom_runtimeInvalidationTracker, SASPlatformContextInstance, SASPlatformContext, SASNumber, SASMutableSet<ObjectType>, SASMutableDictionary<KeyType, ObjectType>, SASLong, SASKotlinThrowable, SASKotlinRuntimeException, SASKotlinIllegalStateException, SASKotlinIllegalArgumentException, SASKotlinException, SASKotlinCancellationException, SASKotlinByteIterator, SASKotlinByteArray, SASKotlinArray<T>, SASInt, SASFloat, SASEntry, SASDouble, SASDatabaseFilesCompanion, SASDatabaseFiles, SASByte, SASBoolean, SASBase, NSString, NSSet<ObjectType>, NSObject, NSNumber, NSMutableSet<ObjectType>, NSMutableDictionary<KeyType, ObjectType>, NSMutableArray<ObjectType>, NSError, NSDictionary<KeyType, ObjectType>, NSArray<ObjectType>;

@protocol SASSqliteSQLiteStatement, SASSqliteSQLiteConnection, SASSkie_DispatcherDelegate, SASSharedStorage, SASRoom_runtimeRoomOpenDelegateMarker, SASRoom_runtimeRoomDatabaseConstructor, SASRoom_runtimeAutoMigrationSpec, SASKotlinx_coroutines_coreStateFlow, SASKotlinx_coroutines_coreSharedFlow, SASKotlinx_coroutines_coreRunnable, SASKotlinx_coroutines_coreMutableStateFlow, SASKotlinx_coroutines_coreMutableSharedFlow, SASKotlinx_coroutines_coreFlowCollector, SASKotlinx_coroutines_coreFlow, SASKotlinx_coroutines_coreCoroutineScope, SASKotlinSuspendFunction1, SASKotlinKDeclarationContainer, SASKotlinKClassifier, SASKotlinKClass, SASKotlinKAnnotatedElement, SASKotlinIterator, SASKotlinFunction, SASKotlinCoroutineContextKey, SASKotlinCoroutineContextElement, SASKotlinCoroutineContext, SASKotlinAutoCloseable, NSCopying;

// Due to an Obj-C/Swift interop limitation, SKIE cannot generate Swift types with a lambda type argument.
// Example of such type is: A<() -> Unit> where A<T> is a generic class.
// To avoid compilation errors SKIE replaces these type arguments with __SkieLambdaErrorType, resulting in A<__SkieLambdaErrorType>.
// Generated declarations that reference __SkieLambdaErrorType cannot be called in any way and the __SkieLambdaErrorType class cannot be used.
// The original declarations can still be used in the same way as other declarations hidden by SKIE (and with the same limitations as without SKIE).
@interface __SkieLambdaErrorType : NSObject
- (instancetype _Nonnull)init __attribute__((unavailable));
+ (instancetype _Nonnull)new __attribute__((unavailable));
@end

// Due to an Obj-C/Swift interop limitation, SKIE cannot generate Swift code that uses external Obj-C types for which SKIE doesn't know a fully qualified name.
// This problem occurs when custom Cinterop bindings are used because those do not contain the name of the Framework that provides implementation for those binding.
// The name can be configured manually using the SKIE Gradle configuration key 'ClassInterop.CInteropFrameworkName' in the same way as other SKIE features.
// To avoid compilation errors SKIE replaces types with unknown Framework name with __SkieUnknownCInteropFrameworkErrorType.
// Generated declarations that reference __SkieUnknownCInteropFrameworkErrorType cannot be called in any way and the __SkieUnknownCInteropFrameworkErrorType class cannot be used.
@interface __SkieUnknownCInteropFrameworkErrorType : NSObject
- (instancetype _Nonnull)init __attribute__((unavailable));
+ (instancetype _Nonnull)new __attribute__((unavailable));
@end


NS_ASSUME_NONNULL_BEGIN
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunknown-warning-option"
#pragma clang diagnostic ignored "-Wincompatible-property-type"
#pragma clang diagnostic ignored "-Wnullability"

#pragma push_macro("_Nullable_result")
#if !__has_feature(nullability_nullable_result)
#undef _Nullable_result
#define _Nullable_result _Nullable
#endif

__attribute__((swift_name("KotlinBase")))
@interface SASBase : NSObject
- (instancetype)init __attribute__((unavailable));
+ (instancetype)new __attribute__((unavailable));
+ (void)initialize __attribute__((objc_requires_super));
@end

@interface SASBase (SASBaseCopying) <NSCopying>
@end

__attribute__((swift_name("KotlinMutableSet")))
@interface SASMutableSet<ObjectType> : NSMutableSet<ObjectType>
@end

__attribute__((swift_name("KotlinMutableDictionary")))
@interface SASMutableDictionary<KeyType, ObjectType> : NSMutableDictionary<KeyType, ObjectType>
@end

@interface NSError (NSErrorSASKotlinException)
@property (readonly) id _Nullable kotlinException;
@end

__attribute__((swift_name("KotlinNumber")))
@interface SASNumber : NSNumber
- (instancetype)initWithChar:(char)value __attribute__((unavailable));
- (instancetype)initWithUnsignedChar:(unsigned char)value __attribute__((unavailable));
- (instancetype)initWithShort:(short)value __attribute__((unavailable));
- (instancetype)initWithUnsignedShort:(unsigned short)value __attribute__((unavailable));
- (instancetype)initWithInt:(int)value __attribute__((unavailable));
- (instancetype)initWithUnsignedInt:(unsigned int)value __attribute__((unavailable));
- (instancetype)initWithLong:(long)value __attribute__((unavailable));
- (instancetype)initWithUnsignedLong:(unsigned long)value __attribute__((unavailable));
- (instancetype)initWithLongLong:(long long)value __attribute__((unavailable));
- (instancetype)initWithUnsignedLongLong:(unsigned long long)value __attribute__((unavailable));
- (instancetype)initWithFloat:(float)value __attribute__((unavailable));
- (instancetype)initWithDouble:(double)value __attribute__((unavailable));
- (instancetype)initWithBool:(BOOL)value __attribute__((unavailable));
- (instancetype)initWithInteger:(NSInteger)value __attribute__((unavailable));
- (instancetype)initWithUnsignedInteger:(NSUInteger)value __attribute__((unavailable));
+ (instancetype)numberWithChar:(char)value __attribute__((unavailable));
+ (instancetype)numberWithUnsignedChar:(unsigned char)value __attribute__((unavailable));
+ (instancetype)numberWithShort:(short)value __attribute__((unavailable));
+ (instancetype)numberWithUnsignedShort:(unsigned short)value __attribute__((unavailable));
+ (instancetype)numberWithInt:(int)value __attribute__((unavailable));
+ (instancetype)numberWithUnsignedInt:(unsigned int)value __attribute__((unavailable));
+ (instancetype)numberWithLong:(long)value __attribute__((unavailable));
+ (instancetype)numberWithUnsignedLong:(unsigned long)value __attribute__((unavailable));
+ (instancetype)numberWithLongLong:(long long)value __attribute__((unavailable));
+ (instancetype)numberWithUnsignedLongLong:(unsigned long long)value __attribute__((unavailable));
+ (instancetype)numberWithFloat:(float)value __attribute__((unavailable));
+ (instancetype)numberWithDouble:(double)value __attribute__((unavailable));
+ (instancetype)numberWithBool:(BOOL)value __attribute__((unavailable));
+ (instancetype)numberWithInteger:(NSInteger)value __attribute__((unavailable));
+ (instancetype)numberWithUnsignedInteger:(NSUInteger)value __attribute__((unavailable));
@end

__attribute__((swift_name("KotlinByte")))
@interface SASByte : SASNumber
- (instancetype)initWithChar:(char)value;
+ (instancetype)numberWithChar:(char)value;
@end

__attribute__((swift_name("KotlinUByte")))
@interface SASUByte : SASNumber
- (instancetype)initWithUnsignedChar:(unsigned char)value;
+ (instancetype)numberWithUnsignedChar:(unsigned char)value;
@end

__attribute__((swift_name("KotlinShort")))
@interface SASShort : SASNumber
- (instancetype)initWithShort:(short)value;
+ (instancetype)numberWithShort:(short)value;
@end

__attribute__((swift_name("KotlinUShort")))
@interface SASUShort : SASNumber
- (instancetype)initWithUnsignedShort:(unsigned short)value;
+ (instancetype)numberWithUnsignedShort:(unsigned short)value;
@end

__attribute__((swift_name("KotlinInt")))
@interface SASInt : SASNumber
- (instancetype)initWithInt:(int)value;
+ (instancetype)numberWithInt:(int)value;
@end

__attribute__((swift_name("KotlinUInt")))
@interface SASUInt : SASNumber
- (instancetype)initWithUnsignedInt:(unsigned int)value;
+ (instancetype)numberWithUnsignedInt:(unsigned int)value;
@end

__attribute__((swift_name("KotlinLong")))
@interface SASLong : SASNumber
- (instancetype)initWithLongLong:(long long)value;
+ (instancetype)numberWithLongLong:(long long)value;
@end

__attribute__((swift_name("KotlinULong")))
@interface SASULong : SASNumber
- (instancetype)initWithUnsignedLongLong:(unsigned long long)value;
+ (instancetype)numberWithUnsignedLongLong:(unsigned long long)value;
@end

__attribute__((swift_name("KotlinFloat")))
@interface SASFloat : SASNumber
- (instancetype)initWithFloat:(float)value;
+ (instancetype)numberWithFloat:(float)value;
@end

__attribute__((swift_name("KotlinDouble")))
@interface SASDouble : SASNumber
- (instancetype)initWithDouble:(double)value;
+ (instancetype)numberWithDouble:(double)value;
@end

__attribute__((swift_name("KotlinBoolean")))
@interface SASBoolean : SASNumber
- (instancetype)initWithBool:(BOOL)value;
+ (instancetype)numberWithBool:(BOOL)value;
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieColdFlowIterator")))
@interface SASSkieColdFlowIterator<E> : SASBase
- (instancetype)initWithFlow:(id<SASKotlinx_coroutines_coreFlow>)flow __attribute__((swift_name("init(flow:)"))) __attribute__((objc_designated_initializer));
- (void)cancel __attribute__((swift_name("cancel()")));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)hasNextWithCompletionHandler:(void (^)(SASBoolean * _Nullable, NSError * _Nullable))completionHandler __attribute__((swift_name("hasNext(completionHandler:)")));
- (E _Nullable)next __attribute__((swift_name("next()")));
@end

__attribute__((swift_name("Kotlinx_coroutines_coreFlow")))
@protocol SASKotlinx_coroutines_coreFlow
@required

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinFlow")))
@interface SASSkieKotlinFlow<__covariant T> : SASBase <SASKotlinx_coroutines_coreFlow>
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
@end

__attribute__((swift_name("Kotlinx_coroutines_coreSharedFlow")))
@protocol SASKotlinx_coroutines_coreSharedFlow <SASKotlinx_coroutines_coreFlow>
@required
@property (readonly) NSArray<id> *replayCache __attribute__((swift_name("replayCache")));
@end

__attribute__((swift_name("Kotlinx_coroutines_coreFlowCollector")))
@protocol SASKotlinx_coroutines_coreFlowCollector
@required

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)emitValue:(id _Nullable)value completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("emit(value:completionHandler:)")));
@end

__attribute__((swift_name("Kotlinx_coroutines_coreMutableSharedFlow")))
@protocol SASKotlinx_coroutines_coreMutableSharedFlow <SASKotlinx_coroutines_coreSharedFlow, SASKotlinx_coroutines_coreFlowCollector>
@required

/**
 * @note annotations
 *   kotlinx.coroutines.ExperimentalCoroutinesApi
*/
- (void)resetReplayCache __attribute__((swift_name("resetReplayCache()")));
- (BOOL)tryEmitValue:(id _Nullable)value __attribute__((swift_name("tryEmit(value:)")));
@property (readonly) id<SASKotlinx_coroutines_coreStateFlow> subscriptionCount __attribute__((swift_name("subscriptionCount")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinMutableSharedFlow")))
@interface SASSkieKotlinMutableSharedFlow<T> : SASBase <SASKotlinx_coroutines_coreMutableSharedFlow>
@property (readonly) NSArray<T> *replayCache __attribute__((swift_name("replayCache")));
@property (readonly) id<SASKotlinx_coroutines_coreStateFlow> subscriptionCount __attribute__((swift_name("subscriptionCount")));
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreMutableSharedFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)emitValue:(T)value completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("emit(value:completionHandler:)")));

/**
 * @note annotations
 *   kotlinx.coroutines.ExperimentalCoroutinesApi
*/
- (void)resetReplayCache __attribute__((swift_name("resetReplayCache()")));
- (BOOL)tryEmitValue:(T)value __attribute__((swift_name("tryEmit(value:)")));
@end

__attribute__((swift_name("Kotlinx_coroutines_coreStateFlow")))
@protocol SASKotlinx_coroutines_coreStateFlow <SASKotlinx_coroutines_coreSharedFlow>
@required
@property (readonly) id _Nullable value __attribute__((swift_name("value")));
@end

__attribute__((swift_name("Kotlinx_coroutines_coreMutableStateFlow")))
@protocol SASKotlinx_coroutines_coreMutableStateFlow <SASKotlinx_coroutines_coreStateFlow, SASKotlinx_coroutines_coreMutableSharedFlow>
@required
- (void)setValue:(id _Nullable)value __attribute__((swift_name("setValue(_:)")));
- (BOOL)compareAndSetExpect:(id _Nullable)expect update:(id _Nullable)update __attribute__((swift_name("compareAndSet(expect:update:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinMutableStateFlow")))
@interface SASSkieKotlinMutableStateFlow<T> : SASBase <SASKotlinx_coroutines_coreMutableStateFlow>
@property (readonly) NSArray<T> *replayCache __attribute__((swift_name("replayCache")));
@property (readonly) id<SASKotlinx_coroutines_coreStateFlow> subscriptionCount __attribute__((swift_name("subscriptionCount")));
@property T value __attribute__((swift_name("value")));
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreMutableStateFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
- (BOOL)compareAndSetExpect:(T)expect update:(T)update __attribute__((swift_name("compareAndSet(expect:update:)")));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)emitValue:(T)value completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("emit(value:completionHandler:)")));

/**
 * @note annotations
 *   kotlinx.coroutines.ExperimentalCoroutinesApi
*/
- (void)resetReplayCache __attribute__((swift_name("resetReplayCache()")));
- (BOOL)tryEmitValue:(T)value __attribute__((swift_name("tryEmit(value:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinOptionalFlow")))
@interface SASSkieKotlinOptionalFlow<__covariant T> : SASBase <SASKotlinx_coroutines_coreFlow>
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinOptionalMutableSharedFlow")))
@interface SASSkieKotlinOptionalMutableSharedFlow<T> : SASBase <SASKotlinx_coroutines_coreMutableSharedFlow>
@property (readonly) NSArray<id> *replayCache __attribute__((swift_name("replayCache")));
@property (readonly) id<SASKotlinx_coroutines_coreStateFlow> subscriptionCount __attribute__((swift_name("subscriptionCount")));
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreMutableSharedFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)emitValue:(T _Nullable)value completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("emit(value:completionHandler:)")));

/**
 * @note annotations
 *   kotlinx.coroutines.ExperimentalCoroutinesApi
*/
- (void)resetReplayCache __attribute__((swift_name("resetReplayCache()")));
- (BOOL)tryEmitValue:(T _Nullable)value __attribute__((swift_name("tryEmit(value:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinOptionalMutableStateFlow")))
@interface SASSkieKotlinOptionalMutableStateFlow<T> : SASBase <SASKotlinx_coroutines_coreMutableStateFlow>
@property (readonly) NSArray<id> *replayCache __attribute__((swift_name("replayCache")));
@property (readonly) id<SASKotlinx_coroutines_coreStateFlow> subscriptionCount __attribute__((swift_name("subscriptionCount")));
@property T _Nullable value __attribute__((swift_name("value")));
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreMutableStateFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
- (BOOL)compareAndSetExpect:(T _Nullable)expect update:(T _Nullable)update __attribute__((swift_name("compareAndSet(expect:update:)")));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)emitValue:(T _Nullable)value completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("emit(value:completionHandler:)")));

/**
 * @note annotations
 *   kotlinx.coroutines.ExperimentalCoroutinesApi
*/
- (void)resetReplayCache __attribute__((swift_name("resetReplayCache()")));
- (BOOL)tryEmitValue:(T _Nullable)value __attribute__((swift_name("tryEmit(value:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinOptionalSharedFlow")))
@interface SASSkieKotlinOptionalSharedFlow<__covariant T> : SASBase <SASKotlinx_coroutines_coreSharedFlow>
@property (readonly) NSArray<id> *replayCache __attribute__((swift_name("replayCache")));
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreSharedFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinOptionalStateFlow")))
@interface SASSkieKotlinOptionalStateFlow<__covariant T> : SASBase <SASKotlinx_coroutines_coreStateFlow>
@property (readonly) NSArray<id> *replayCache __attribute__((swift_name("replayCache")));
@property (readonly) T _Nullable value __attribute__((swift_name("value")));
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreStateFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinSharedFlow")))
@interface SASSkieKotlinSharedFlow<__covariant T> : SASBase <SASKotlinx_coroutines_coreSharedFlow>
@property (readonly) NSArray<T> *replayCache __attribute__((swift_name("replayCache")));
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreSharedFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SkieKotlinStateFlow")))
@interface SASSkieKotlinStateFlow<__covariant T> : SASBase <SASKotlinx_coroutines_coreStateFlow>
@property (readonly) NSArray<T> *replayCache __attribute__((swift_name("replayCache")));
@property (readonly) T value __attribute__((swift_name("value")));
- (instancetype)initWithDelegate:(id<SASKotlinx_coroutines_coreStateFlow>)delegate __attribute__((swift_name("init(_:)"))) __attribute__((objc_designated_initializer));

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)collectCollector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("collect(collector:completionHandler:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("Skie_CancellationHandler")))
@interface SASSkie_CancellationHandler : SASBase
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (void)cancel __attribute__((swift_name("cancel()")));
@end

__attribute__((swift_name("Skie_DispatcherDelegate")))
@protocol SASSkie_DispatcherDelegate
@required
- (void)dispatchBlock:(id<SASKotlinx_coroutines_coreRunnable>)block __attribute__((swift_name("dispatch(block:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("Skie_SuspendHandler")))
@interface SASSkie_SuspendHandler : SASBase
- (instancetype)initWithCancellationHandler:(SASSkie_CancellationHandler *)cancellationHandler dispatcherDelegate:(id<SASSkie_DispatcherDelegate>)dispatcherDelegate onResult:(void (^)(SASSkie_SuspendResult *))onResult __attribute__((swift_name("init(cancellationHandler:dispatcherDelegate:onResult:)"))) __attribute__((objc_designated_initializer));
@end

__attribute__((swift_name("Skie_SuspendResult")))
@interface SASSkie_SuspendResult : SASBase
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("Skie_SuspendResult.Canceled")))
@interface SASSkie_SuspendResultCanceled : SASSkie_SuspendResult
@property (class, readonly, getter=shared) SASSkie_SuspendResultCanceled *shared __attribute__((swift_name("shared")));
+ (instancetype)alloc __attribute__((unavailable));
+ (instancetype)allocWithZone:(struct _NSZone *)zone __attribute__((unavailable));
+ (instancetype)canceled __attribute__((swift_name("init()")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("Skie_SuspendResult.Error")))
@interface SASSkie_SuspendResultError : SASSkie_SuspendResult
@property (readonly) NSError *error __attribute__((swift_name("error")));
- (instancetype)initWithError:(NSError *)error __attribute__((swift_name("init(error:)"))) __attribute__((objc_designated_initializer));
- (SASSkie_SuspendResultError *)doCopyError:(NSError *)error __attribute__((swift_name("doCopy(error:)")));
- (BOOL)isEqual:(id _Nullable)other __attribute__((swift_name("isEqual(_:)")));
- (NSUInteger)hash __attribute__((swift_name("hash()")));
- (NSString *)description __attribute__((swift_name("description()")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("Skie_SuspendResult.Success")))
@interface SASSkie_SuspendResultSuccess : SASSkie_SuspendResult
@property (readonly) id _Nullable value __attribute__((swift_name("value")));
- (instancetype)initWithValue:(id _Nullable)value __attribute__((swift_name("init(value:)"))) __attribute__((objc_designated_initializer));
- (SASSkie_SuspendResultSuccess *)doCopyValue:(id _Nullable)value __attribute__((swift_name("doCopy(value:)")));
- (BOOL)isEqual:(id _Nullable)other __attribute__((swift_name("isEqual(_:)")));
- (NSUInteger)hash __attribute__((swift_name("hash()")));
- (NSString *)description __attribute__((swift_name("description()")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("Entry")))
@interface SASEntry : SASBase
@property (readonly) NSString *key __attribute__((swift_name("key")));
@property (readonly) NSString * _Nullable value __attribute__((swift_name("value")));
- (instancetype)initWithKey:(NSString *)key value:(NSString * _Nullable)value __attribute__((swift_name("init(key:value:)"))) __attribute__((objc_designated_initializer));
- (SASEntry *)doCopyKey:(NSString *)key value:(NSString * _Nullable)value __attribute__((swift_name("doCopy(key:value:)")));
- (BOOL)isEqual:(id _Nullable)other __attribute__((swift_name("isEqual(_:)")));
- (NSUInteger)hash __attribute__((swift_name("hash()")));
- (NSString *)description __attribute__((swift_name("description()")));
@end

__attribute__((swift_name("PlatformContext")))
@interface SASPlatformContext : SASBase
@property (class, readonly, getter=companion) SASPlatformContextInstance *companion __attribute__((swift_name("companion")));
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("PlatformContext.Instance")))
@interface SASPlatformContextInstance : SASPlatformContext
@property (class, readonly, getter=shared) SASPlatformContextInstance *shared __attribute__((swift_name("shared")));
+ (instancetype)alloc __attribute__((unavailable));
+ (instancetype)allocWithZone:(struct _NSZone *)zone __attribute__((unavailable));
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer)) __attribute__((unavailable));
+ (instancetype)new __attribute__((unavailable));
+ (instancetype)instance __attribute__((swift_name("init()")));
@end

__attribute__((swift_name("SharedStorage")))
@protocol SASSharedStorage
@required

/**
 * @note This method converts instances of StorageException, CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)clearWithCompletionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("clear(completionHandler:)")));

/**
 * @note This method converts instances of StorageException, CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)getKeysWithCompletionHandler:(void (^)(NSArray<NSString *> * _Nullable, NSError * _Nullable))completionHandler __attribute__((swift_name("getKeys(completionHandler:)")));

/**
 * @note This method converts instances of StorageException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (id<SASKotlinx_coroutines_coreFlow> _Nullable)getKeysFlowAndReturnError:(NSError * _Nullable * _Nullable)error __attribute__((swift_name("getKeysFlow()")));

/**
 * @note This method converts instances of StorageException, CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)getValuesKeys:(NSArray<NSString *> *)keys completionHandler:(void (^)(NSArray<SASEntry *> * _Nullable, NSError * _Nullable))completionHandler __attribute__((swift_name("getValues(keys:completionHandler:)")));

/**
 * @note This method converts instances of StorageException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (id<SASKotlinx_coroutines_coreFlow> _Nullable)getValuesFlowKeys:(NSArray<NSString *> *)keys error:(NSError * _Nullable * _Nullable)error __attribute__((swift_name("getValuesFlow(keys:)")));

/**
 * @note This method converts instances of StorageException, CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)removeValuesKeys:(NSArray<NSString *> *)keys completionHandler:(void (^)(NSError * _Nullable))completionHandler __attribute__((swift_name("removeValues(keys:completionHandler:)")));

/**
 * @note This method converts instances of StorageException, CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)setValuesEntries:(NSArray<SASEntry *> *)entries completionHandler:(void (^)(NSArray<SASEntry *> * _Nullable, NSError * _Nullable))completionHandler __attribute__((swift_name("setValues(entries:completionHandler:)")));
@end

__attribute__((swift_name("KotlinThrowable")))
@interface SASKotlinThrowable : SASBase
@property (readonly) SASKotlinThrowable * _Nullable cause __attribute__((swift_name("cause")));
@property (readonly) NSString * _Nullable message __attribute__((swift_name("message")));
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (instancetype)initWithMessage:(NSString * _Nullable)message __attribute__((swift_name("init(message:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithCause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(cause:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithMessage:(NSString * _Nullable)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer));

/**
 * @note annotations
 *   kotlin.experimental.ExperimentalNativeApi
*/
- (SASKotlinArray<NSString *> *)getStackTrace __attribute__((swift_name("getStackTrace()")));
- (void)printStackTrace __attribute__((swift_name("printStackTrace()")));
- (NSString *)description __attribute__((swift_name("description()")));
- (NSError *)asError __attribute__((swift_name("asError()")));
@end

__attribute__((swift_name("KotlinException")))
@interface SASKotlinException : SASKotlinThrowable
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (instancetype)initWithMessage:(NSString * _Nullable)message __attribute__((swift_name("init(message:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithCause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(cause:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithMessage:(NSString * _Nullable)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer));
@end

__attribute__((swift_name("StorageException")))
@interface SASStorageException : SASKotlinException
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer)) __attribute__((unavailable));
+ (instancetype)new __attribute__((unavailable));
- (instancetype)initWithMessage:(NSString * _Nullable)message __attribute__((swift_name("init(message:)"))) __attribute__((objc_designated_initializer)) __attribute__((unavailable));
- (instancetype)initWithCause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(cause:)"))) __attribute__((objc_designated_initializer)) __attribute__((unavailable));
- (instancetype)initWithMessage:(NSString * _Nullable)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer)) __attribute__((unavailable));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("StorageException.OtherException")))
@interface SASStorageExceptionOtherException : SASStorageException
- (instancetype)initWithMessage:(NSString *)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("StorageException.SqliteException")))
@interface SASStorageExceptionSqliteException : SASStorageException
- (instancetype)initWithMessage:(NSString *)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("DatabaseFiles")))
@interface SASDatabaseFiles : SASBase
@property (class, readonly, getter=companion) SASDatabaseFilesCompanion *companion __attribute__((swift_name("companion")));
@property (readonly) NSString *databaseFileName __attribute__((swift_name("databaseFileName")));
@property (readonly) NSString *databaseName __attribute__((swift_name("databaseName")));
@property (readonly) NSString *directoryAbsolutePath __attribute__((swift_name("directoryAbsolutePath")));
@property (readonly) NSString *fileAbsolutePath __attribute__((swift_name("fileAbsolutePath")));
- (BOOL)isEqual:(id _Nullable)other __attribute__((swift_name("isEqual(_:)")));
- (NSUInteger)hash __attribute__((swift_name("hash()")));
- (NSString *)description __attribute__((swift_name("description()")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("DatabaseFiles.Companion")))
@interface SASDatabaseFilesCompanion : SASBase
@property (class, readonly, getter=shared) SASDatabaseFilesCompanion *shared __attribute__((swift_name("shared")));
+ (instancetype)alloc __attribute__((unavailable));
+ (instancetype)allocWithZone:(struct _NSZone *)zone __attribute__((unavailable));
+ (instancetype)companion __attribute__((swift_name("init()")));
@end

__attribute__((swift_name("Room_runtimeRoomDatabase")))
@interface SASRoom_runtimeRoomDatabase : SASBase
@property (readonly) SASRoom_runtimeInvalidationTracker *invalidationTracker __attribute__((swift_name("invalidationTracker")));
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (void)close __attribute__((swift_name("close()")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
*/
- (NSArray<SASRoom_runtimeMigration *> *)createAutoMigrationsAutoMigrationSpecs:(NSDictionary<id<SASKotlinKClass>, id<SASRoom_runtimeAutoMigrationSpec>> *)autoMigrationSpecs __attribute__((swift_name("createAutoMigrations(autoMigrationSpecs:)")));

/**
 * @note This method has protected visibility in Kotlin source and is intended only for use by subclasses.
*/
- (SASRoom_runtimeInvalidationTracker *)createInvalidationTracker __attribute__((swift_name("createInvalidationTracker()")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
 * @note This method has protected visibility in Kotlin source and is intended only for use by subclasses.
*/
- (id<SASRoom_runtimeRoomOpenDelegateMarker>)createOpenDelegate __attribute__((swift_name("createOpenDelegate()")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP])
*/
- (id<SASKotlinx_coroutines_coreCoroutineScope>)getCoroutineScope __attribute__((swift_name("getCoroutineScope()")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
*/
- (NSSet<id<SASKotlinKClass>> *)getRequiredAutoMigrationSpecClasses __attribute__((swift_name("getRequiredAutoMigrationSpecClasses()")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
 * @note This method has protected visibility in Kotlin source and is intended only for use by subclasses.
*/
- (NSDictionary<id<SASKotlinKClass>, NSArray<id<SASKotlinKClass>> *> *)getRequiredTypeConverterClasses __attribute__((swift_name("getRequiredTypeConverterClasses()")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
*/
- (id)getTypeConverterKlass:(id<SASKotlinKClass>)klass __attribute__((swift_name("getTypeConverter(klass:)")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
 * @note This method has protected visibility in Kotlin source and is intended only for use by subclasses.
*/
- (void)internalInitInvalidationTrackerConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("internalInitInvalidationTracker(connection:)")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP])
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)useConnectionIsReadOnly:(BOOL)isReadOnly block:(id<SASKotlinSuspendFunction1>)block completionHandler:(void (^)(id _Nullable_result, NSError * _Nullable))completionHandler __attribute__((swift_name("useConnection(isReadOnly:block:completionHandler:)")));
@end

__attribute__((swift_name("StorageDatabase")))
@interface SASStorageDatabase : SASRoom_runtimeRoomDatabase
@property (class, readonly, getter=companion) SASStorageDatabaseCompanion *companion __attribute__((swift_name("companion")));
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("StorageDatabase.Companion")))
@interface SASStorageDatabaseCompanion : SASBase
@property (class, readonly, getter=shared) SASStorageDatabaseCompanion *shared __attribute__((swift_name("shared")));
+ (instancetype)alloc __attribute__((unavailable));
+ (instancetype)allocWithZone:(struct _NSZone *)zone __attribute__((unavailable));
+ (instancetype)companion __attribute__((swift_name("init()")));
@end

__attribute__((swift_name("Room_runtimeRoomDatabaseConstructor")))
@protocol SASRoom_runtimeRoomDatabaseConstructor
@required
- (SASRoom_runtimeRoomDatabase *)initialize __attribute__((swift_name("initialize()")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("StorageDatabaseConstructor")))
@interface SASStorageDatabaseConstructor : SASBase <SASRoom_runtimeRoomDatabaseConstructor>
@property (class, readonly, getter=shared) SASStorageDatabaseConstructor *shared __attribute__((swift_name("shared")));
+ (instancetype)alloc __attribute__((unavailable));
+ (instancetype)allocWithZone:(struct _NSZone *)zone __attribute__((unavailable));
+ (instancetype)storageDatabaseConstructor __attribute__((swift_name("init()")));
- (SASStorageDatabase *)initialize __attribute__((swift_name("initialize()")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("StorageDatabase_Impl")))
@interface SASStorageDatabase_Impl : SASStorageDatabase
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (NSArray<SASRoom_runtimeMigration *> *)createAutoMigrationsAutoMigrationSpecs:(NSDictionary<id<SASKotlinKClass>, id<SASRoom_runtimeAutoMigrationSpec>> *)autoMigrationSpecs __attribute__((swift_name("createAutoMigrations(autoMigrationSpecs:)")));

/**
 * @note This method has protected visibility in Kotlin source and is intended only for use by subclasses.
*/
- (SASRoom_runtimeInvalidationTracker *)createInvalidationTracker __attribute__((swift_name("createInvalidationTracker()")));

/**
 * @note This method has protected visibility in Kotlin source and is intended only for use by subclasses.
*/
- (SASRoom_runtimeRoomOpenDelegate *)createOpenDelegate __attribute__((swift_name("createOpenDelegate()")));
- (NSSet<id<SASKotlinKClass>> *)getRequiredAutoMigrationSpecClasses __attribute__((swift_name("getRequiredAutoMigrationSpecClasses()")));

/**
 * @note This method has protected visibility in Kotlin source and is intended only for use by subclasses.
*/
- (NSDictionary<id<SASKotlinKClass>, NSArray<id<SASKotlinKClass>> *> *)getRequiredTypeConverterClasses __attribute__((swift_name("getRequiredTypeConverterClasses()")));
@end

@interface SASDatabaseFilesCompanion (Extensions)

/**
 * @note This method converts instances of IllegalStateException, IllegalArgumentException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (SASDatabaseFiles * _Nullable)ofContext:(SASPlatformContext *)context databaseName:(NSString *)databaseName error:(NSError * _Nullable * _Nullable)error __attribute__((swift_name("of(context:databaseName:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("SharedStorage_appleKt")))
@interface SASSharedStorage_appleKt : SASBase
+ (id<SASSharedStorage>)SharedStorageContext:(SASPlatformContext *)context databaseName:(NSString *)databaseName __attribute__((swift_name("SharedStorage(context:databaseName:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("__SkieSuspendWrappersKt")))
@interface SAS__SkieSuspendWrappersKt : SASBase
+ (void)Skie_Suspend__0__hasNextDispatchReceiver:(SASSkieColdFlowIterator<id> *)dispatchReceiver suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__0__hasNext(dispatchReceiver:suspendHandler:)")));
+ (void)Skie_Suspend__10__refreshDispatchReceiver:(SASRoom_runtimeInvalidationTracker *)dispatchReceiver tables:(SASKotlinArray<NSString *> *)tables suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__10__refresh(dispatchReceiver:tables:suspendHandler:)")));
+ (void)Skie_Suspend__1__collectDispatchReceiver:(id<SASKotlinx_coroutines_coreFlow>)dispatchReceiver collector:(id<SASKotlinx_coroutines_coreFlowCollector>)collector suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__1__collect(dispatchReceiver:collector:suspendHandler:)")));
+ (void)Skie_Suspend__2__emitDispatchReceiver:(id<SASKotlinx_coroutines_coreFlowCollector>)dispatchReceiver value:(id _Nullable)value suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__2__emit(dispatchReceiver:value:suspendHandler:)")));
+ (void)Skie_Suspend__3__clearDispatchReceiver:(id<SASSharedStorage>)dispatchReceiver suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__3__clear(dispatchReceiver:suspendHandler:)")));
+ (void)Skie_Suspend__4__getKeysDispatchReceiver:(id<SASSharedStorage>)dispatchReceiver suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__4__getKeys(dispatchReceiver:suspendHandler:)")));
+ (void)Skie_Suspend__5__getValuesDispatchReceiver:(id<SASSharedStorage>)dispatchReceiver keys:(NSArray<NSString *> *)keys suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__5__getValues(dispatchReceiver:keys:suspendHandler:)")));
+ (void)Skie_Suspend__6__removeValuesDispatchReceiver:(id<SASSharedStorage>)dispatchReceiver keys:(NSArray<NSString *> *)keys suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__6__removeValues(dispatchReceiver:keys:suspendHandler:)")));
+ (void)Skie_Suspend__7__setValuesDispatchReceiver:(id<SASSharedStorage>)dispatchReceiver entries:(NSArray<SASEntry *> *)entries suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__7__setValues(dispatchReceiver:entries:suspendHandler:)")));
+ (void)Skie_Suspend__8__useConnectionDispatchReceiver:(SASRoom_runtimeRoomDatabase *)dispatchReceiver isReadOnly:(BOOL)isReadOnly block:(id<SASKotlinSuspendFunction1>)block suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__8__useConnection(dispatchReceiver:isReadOnly:block:suspendHandler:)")));
+ (void)Skie_Suspend__9__invokeDispatchReceiver:(id<SASKotlinSuspendFunction1>)dispatchReceiver p1:(id _Nullable)p1 suspendHandler:(SASSkie_SuspendHandler *)suspendHandler __attribute__((swift_name("Skie_Suspend__9__invoke(dispatchReceiver:p1:suspendHandler:)")));
@end

__attribute__((swift_name("KotlinRuntimeException")))
@interface SASKotlinRuntimeException : SASKotlinException
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (instancetype)initWithMessage:(NSString * _Nullable)message __attribute__((swift_name("init(message:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithCause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(cause:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithMessage:(NSString * _Nullable)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer));
@end

__attribute__((swift_name("KotlinIllegalStateException")))
@interface SASKotlinIllegalStateException : SASKotlinRuntimeException
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (instancetype)initWithMessage:(NSString * _Nullable)message __attribute__((swift_name("init(message:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithCause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(cause:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithMessage:(NSString * _Nullable)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer));
@end


/**
 * @note annotations
 *   kotlin.SinceKotlin(version="1.4")
*/
__attribute__((swift_name("KotlinCancellationException")))
@interface SASKotlinCancellationException : SASKotlinIllegalStateException
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (instancetype)initWithMessage:(NSString * _Nullable)message __attribute__((swift_name("init(message:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithCause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(cause:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithMessage:(NSString * _Nullable)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer));
@end

__attribute__((swift_name("Kotlinx_coroutines_coreRunnable")))
@protocol SASKotlinx_coroutines_coreRunnable
@required
- (void)run __attribute__((swift_name("run()")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("KotlinArray")))
@interface SASKotlinArray<T> : SASBase
@property (readonly) int32_t size __attribute__((swift_name("size")));
+ (instancetype)arrayWithSize:(int32_t)size init:(T _Nullable (^)(SASInt *))init __attribute__((swift_name("init(size:init:)")));
+ (instancetype)alloc __attribute__((unavailable));
+ (instancetype)allocWithZone:(struct _NSZone *)zone __attribute__((unavailable));
- (T _Nullable)getIndex:(int32_t)index __attribute__((swift_name("get(index:)")));
- (id<SASKotlinIterator>)iterator __attribute__((swift_name("iterator()")));
- (void)setIndex:(int32_t)index value:(T _Nullable)value __attribute__((swift_name("set(index:value:)")));
@end

__attribute__((swift_name("Room_runtimeMigration")))
@interface SASRoom_runtimeMigration : SASBase
@property (readonly) int32_t endVersion __attribute__((swift_name("endVersion")));
@property (readonly) int32_t startVersion __attribute__((swift_name("startVersion")));
- (instancetype)initWithStartVersion:(int32_t)startVersion endVersion:(int32_t)endVersion __attribute__((swift_name("init(startVersion:endVersion:)"))) __attribute__((objc_designated_initializer));
- (void)migrateConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("migrate(connection:)")));
@end

__attribute__((swift_name("KotlinKDeclarationContainer")))
@protocol SASKotlinKDeclarationContainer
@required
@end

__attribute__((swift_name("KotlinKAnnotatedElement")))
@protocol SASKotlinKAnnotatedElement
@required
@end


/**
 * @note annotations
 *   kotlin.SinceKotlin(version="1.1")
*/
__attribute__((swift_name("KotlinKClassifier")))
@protocol SASKotlinKClassifier
@required
@end

__attribute__((swift_name("KotlinKClass")))
@protocol SASKotlinKClass <SASKotlinKDeclarationContainer, SASKotlinKAnnotatedElement, SASKotlinKClassifier>
@required

/**
 * @note annotations
 *   kotlin.SinceKotlin(version="1.1")
*/
- (BOOL)isInstanceValue:(id _Nullable)value __attribute__((swift_name("isInstance(value:)")));
@property (readonly) NSString * _Nullable qualifiedName __attribute__((swift_name("qualifiedName")));
@property (readonly) NSString * _Nullable simpleName __attribute__((swift_name("simpleName")));
@end

__attribute__((swift_name("Room_runtimeAutoMigrationSpec")))
@protocol SASRoom_runtimeAutoMigrationSpec
@required
- (void)onPostMigrateConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("onPostMigrate(connection:)")));
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("Room_runtimeInvalidationTracker")))
@interface SASRoom_runtimeInvalidationTracker : SASBase

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
*/
- (instancetype)initWithDatabase:(SASRoom_runtimeRoomDatabase *)database shadowTablesMap:(NSDictionary<NSString *, NSString *> *)shadowTablesMap viewTables:(NSDictionary<NSString *, NSSet<NSString *> *> *)viewTables tableNames:(SASKotlinArray<NSString *> *)tableNames __attribute__((swift_name("init(database:shadowTablesMap:viewTables:tableNames:)"))) __attribute__((objc_designated_initializer));

/**
 * @note annotations
 *   kotlin.jvm.JvmOverloads
*/
- (id<SASKotlinx_coroutines_coreFlow>)createFlowTables:(SASKotlinArray<NSString *> *)tables emitInitialState:(BOOL)emitInitialState __attribute__((swift_name("createFlow(tables:emitInitialState:)")));

/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP])
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)refreshTables:(SASKotlinArray<NSString *> *)tables completionHandler:(void (^)(SASBoolean * _Nullable, NSError * _Nullable))completionHandler __attribute__((swift_name("refresh(tables:completionHandler:)")));
- (void)refreshAsync __attribute__((swift_name("refreshAsync()")));
@end

__attribute__((swift_name("Room_runtimeRoomOpenDelegateMarker")))
@protocol SASRoom_runtimeRoomOpenDelegateMarker
@required
@end

__attribute__((swift_name("Kotlinx_coroutines_coreCoroutineScope")))
@protocol SASKotlinx_coroutines_coreCoroutineScope
@required
@property (readonly) id<SASKotlinCoroutineContext> coroutineContext __attribute__((swift_name("coroutineContext")));
@end


/**
 * @note annotations
 *   kotlin.SinceKotlin(version="2.0")
*/
__attribute__((swift_name("KotlinAutoCloseable")))
@protocol SASKotlinAutoCloseable
@required
- (void)close __attribute__((swift_name("close()")));
@end

__attribute__((swift_name("SqliteSQLiteConnection")))
@protocol SASSqliteSQLiteConnection <SASKotlinAutoCloseable>
@required
- (BOOL)inTransaction __attribute__((swift_name("inTransaction()")));
- (id<SASSqliteSQLiteStatement>)prepareSql:(NSString *)sql __attribute__((swift_name("prepare(sql:)")));
@end

__attribute__((swift_name("KotlinFunction")))
@protocol SASKotlinFunction
@required
@end

__attribute__((swift_name("KotlinSuspendFunction1")))
@protocol SASKotlinSuspendFunction1 <SASKotlinFunction>
@required

/**
 * @note This method converts instances of CancellationException to errors.
 * Other uncaught Kotlin exceptions are fatal.
*/
- (void)invokeP1:(id _Nullable)p1 completionHandler:(void (^)(id _Nullable_result, NSError * _Nullable))completionHandler __attribute__((swift_name("invoke(p1:completionHandler:)")));
@end


/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
*/
__attribute__((swift_name("Room_runtimeRoomOpenDelegate")))
@interface SASRoom_runtimeRoomOpenDelegate : SASBase <SASRoom_runtimeRoomOpenDelegateMarker>
@property (readonly) NSString *identityHash __attribute__((swift_name("identityHash")));
@property (readonly) NSString *legacyIdentityHash __attribute__((swift_name("legacyIdentityHash")));
@property (readonly) int32_t version __attribute__((swift_name("version")));
- (instancetype)initWithVersion:(int32_t)version identityHash:(NSString *)identityHash legacyIdentityHash:(NSString *)legacyIdentityHash __attribute__((swift_name("init(version:identityHash:legacyIdentityHash:)"))) __attribute__((objc_designated_initializer));
- (void)createAllTablesConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("createAllTables(connection:)")));
- (void)dropAllTablesConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("dropAllTables(connection:)")));
- (void)onCreateConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("onCreate(connection:)")));
- (void)onOpenConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("onOpen(connection:)")));
- (void)onPostMigrateConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("onPostMigrate(connection:)")));
- (void)onPreMigrateConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("onPreMigrate(connection:)")));
- (SASRoom_runtimeRoomOpenDelegateValidationResult *)onValidateSchemaConnection:(id<SASSqliteSQLiteConnection>)connection __attribute__((swift_name("onValidateSchema(connection:)")));
@end

__attribute__((swift_name("KotlinIllegalArgumentException")))
@interface SASKotlinIllegalArgumentException : SASKotlinRuntimeException
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (instancetype)initWithMessage:(NSString * _Nullable)message __attribute__((swift_name("init(message:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithCause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(cause:)"))) __attribute__((objc_designated_initializer));
- (instancetype)initWithMessage:(NSString * _Nullable)message cause:(SASKotlinThrowable * _Nullable)cause __attribute__((swift_name("init(message:cause:)"))) __attribute__((objc_designated_initializer));
@end

__attribute__((swift_name("KotlinIterator")))
@protocol SASKotlinIterator
@required
- (BOOL)hasNext __attribute__((swift_name("hasNext()")));
- (id _Nullable)next __attribute__((swift_name("next()")));
@end


/**
 * @note annotations
 *   kotlin.SinceKotlin(version="1.3")
*/
__attribute__((swift_name("KotlinCoroutineContext")))
@protocol SASKotlinCoroutineContext
@required
- (id _Nullable)foldInitial:(id _Nullable)initial operation:(id _Nullable (^)(id _Nullable, id<SASKotlinCoroutineContextElement>))operation __attribute__((swift_name("fold(initial:operation:)")));
- (id<SASKotlinCoroutineContextElement> _Nullable)getKey:(id<SASKotlinCoroutineContextKey>)key __attribute__((swift_name("get(key:)")));
- (id<SASKotlinCoroutineContext>)minusKeyKey:(id<SASKotlinCoroutineContextKey>)key __attribute__((swift_name("minusKey(key:)")));
- (id<SASKotlinCoroutineContext>)plusContext:(id<SASKotlinCoroutineContext>)context __attribute__((swift_name("plus(context:)")));
@end

__attribute__((swift_name("SqliteSQLiteStatement")))
@protocol SASSqliteSQLiteStatement <SASKotlinAutoCloseable>
@required

/**
 * @param index annotations androidx.annotation.IntRange(from=1.toLong())
*/
- (void)bindBlobIndex:(int32_t)index value:(SASKotlinByteArray *)value __attribute__((swift_name("bindBlob(index:value:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=1.toLong())
*/
- (void)bindBooleanIndex:(int32_t)index value:(BOOL)value __attribute__((swift_name("bindBoolean(index:value:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=1.toLong())
*/
- (void)bindDoubleIndex:(int32_t)index value:(double)value __attribute__((swift_name("bindDouble(index:value:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=1.toLong())
*/
- (void)bindFloatIndex:(int32_t)index value:(float)value __attribute__((swift_name("bindFloat(index:value:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=1.toLong())
*/
- (void)bindIntIndex:(int32_t)index value:(int32_t)value __attribute__((swift_name("bindInt(index:value:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=1.toLong())
*/
- (void)bindLongIndex:(int32_t)index value:(int64_t)value __attribute__((swift_name("bindLong(index:value:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=1.toLong())
*/
- (void)bindNullIndex:(int32_t)index __attribute__((swift_name("bindNull(index:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=1.toLong())
*/
- (void)bindTextIndex:(int32_t)index value:(NSString *)value __attribute__((swift_name("bindText(index:value:)")));
- (void)clearBindings __attribute__((swift_name("clearBindings()")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (SASKotlinByteArray *)getBlobIndex:(int32_t)index __attribute__((swift_name("getBlob(index:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (BOOL)getBooleanIndex:(int32_t)index __attribute__((swift_name("getBoolean(index:)")));
- (int32_t)getColumnCount __attribute__((swift_name("getColumnCount()")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (NSString *)getColumnNameIndex:(int32_t)index __attribute__((swift_name("getColumnName(index:)")));
- (NSArray<NSString *> *)getColumnNames __attribute__((swift_name("getColumnNames()")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (int32_t)getColumnTypeIndex:(int32_t)index __attribute__((swift_name("getColumnType(index:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (double)getDoubleIndex:(int32_t)index __attribute__((swift_name("getDouble(index:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (float)getFloatIndex:(int32_t)index __attribute__((swift_name("getFloat(index:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (int32_t)getIntIndex:(int32_t)index __attribute__((swift_name("getInt(index:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (int64_t)getLongIndex:(int32_t)index __attribute__((swift_name("getLong(index:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (NSString *)getTextIndex:(int32_t)index __attribute__((swift_name("getText(index:)")));

/**
 * @param index annotations androidx.annotation.IntRange(from=0.toLong())
*/
- (BOOL)isNullIndex:(int32_t)index __attribute__((swift_name("isNull(index:)")));
- (void)reset __attribute__((swift_name("reset()")));
- (BOOL)step __attribute__((swift_name("step()")));
@end


/**
 * @note annotations
 *   androidx.annotation.RestrictTo(value=[Scope.LIBRARY_GROUP_PREFIX])
*/
__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("Room_runtimeRoomOpenDelegate.ValidationResult")))
@interface SASRoom_runtimeRoomOpenDelegateValidationResult : SASBase
@property (readonly) NSString * _Nullable expectedFoundMsg __attribute__((swift_name("expectedFoundMsg")));
@property (readonly) BOOL isValid __attribute__((swift_name("isValid")));
- (instancetype)initWithIsValid:(BOOL)isValid expectedFoundMsg:(NSString * _Nullable)expectedFoundMsg __attribute__((swift_name("init(isValid:expectedFoundMsg:)"))) __attribute__((objc_designated_initializer));
@end

__attribute__((swift_name("KotlinCoroutineContextElement")))
@protocol SASKotlinCoroutineContextElement <SASKotlinCoroutineContext>
@required
@property (readonly) id<SASKotlinCoroutineContextKey> key __attribute__((swift_name("key")));
@end

__attribute__((swift_name("KotlinCoroutineContextKey")))
@protocol SASKotlinCoroutineContextKey
@required
@end

__attribute__((objc_subclassing_restricted))
__attribute__((swift_name("KotlinByteArray")))
@interface SASKotlinByteArray : SASBase
@property (readonly) int32_t size __attribute__((swift_name("size")));
+ (instancetype)arrayWithSize:(int32_t)size __attribute__((swift_name("init(size:)")));
+ (instancetype)arrayWithSize:(int32_t)size init:(SASByte *(^)(SASInt *))init __attribute__((swift_name("init(size:init:)")));
+ (instancetype)alloc __attribute__((unavailable));
+ (instancetype)allocWithZone:(struct _NSZone *)zone __attribute__((unavailable));
- (int8_t)getIndex:(int32_t)index __attribute__((swift_name("get(index:)")));
- (SASKotlinByteIterator *)iterator __attribute__((swift_name("iterator()")));
- (void)setIndex:(int32_t)index value:(int8_t)value __attribute__((swift_name("set(index:value:)")));
@end

__attribute__((swift_name("KotlinByteIterator")))
@interface SASKotlinByteIterator : SASBase <SASKotlinIterator>
- (instancetype)init __attribute__((swift_name("init()"))) __attribute__((objc_designated_initializer));
+ (instancetype)new __attribute__((availability(swift, unavailable, message="use object initializers instead")));
- (SASByte *)next __attribute__((swift_name("next()")));
- (int8_t)nextByte __attribute__((swift_name("nextByte()")));
@end

#pragma pop_macro("_Nullable_result")
#pragma clang diagnostic pop
NS_ASSUME_NONNULL_END

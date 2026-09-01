#import <React/RCTBridgeModule.h>

#ifdef RCT_NEW_ARCH_ENABLED
#import <AsyncStorageSpec/AsyncStorageSpec.h>
#endif

@interface AsyncStorage : NSObject <
#ifdef RCT_NEW_ARCH_ENABLED
                              NativeAsyncStorageSpec
#else
                              RCTBridgeModule
#endif
                              >

@end

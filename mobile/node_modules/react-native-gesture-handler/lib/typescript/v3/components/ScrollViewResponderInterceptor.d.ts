import type { PropsWithChildren } from 'react';
import React from 'react';
import type { ScrollViewProps as RNScrollViewProps } from 'react-native';
type KeyboardShouldPersistTaps = RNScrollViewProps['keyboardShouldPersistTaps'];
export type JSResponderContextValue = {
    isRNGHResponderEvent: React.MutableRefObject<boolean>;
    keyboardShouldPersistTaps: KeyboardShouldPersistTaps;
};
export declare const JSResponderContext: React.Context<JSResponderContextValue | null>;
export declare function updateResponderEventValue(jsResponderContext: JSResponderContextValue | null | undefined, value: boolean): void;
export declare function isKeyboardDismissingTap(jsResponderContext: JSResponderContextValue | null | undefined): boolean;
type ScrollViewResponderInterceptorProps = PropsWithChildren<{
    keyboardShouldPersistTaps?: RNScrollViewProps['keyboardShouldPersistTaps'];
}>;
declare const ScrollViewResponderInterceptor: ({ children, keyboardShouldPersistTaps, }: ScrollViewResponderInterceptorProps) => React.JSX.Element;
export default ScrollViewResponderInterceptor;
//# sourceMappingURL=ScrollViewResponderInterceptor.d.ts.map
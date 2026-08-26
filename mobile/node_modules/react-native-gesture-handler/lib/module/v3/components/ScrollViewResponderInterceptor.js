"use strict";

import React, { useCallback, useEffect, useMemo, useRef } from 'react';
import { Keyboard, StyleSheet, View } from 'react-native';
import { jsx as _jsx } from "react/jsx-runtime";
// The listeners are shared by every mounted ScrollView, so attach/detach is
// reference-counted: we subscribe on the first interceptor and tear down only
// once the last one unmounts.
let keyboardTrackerRefCount = 0;
let keyboardTrackerSubscriptions = [];
let isKeyboardVisible = false;
function keyboardIsOpen(height) {
  return height != null && height > 0;
}
function subscribeToKeyboardVisibility() {
  keyboardTrackerRefCount++;
  if (keyboardTrackerRefCount > 1 || Keyboard?.addListener == null) {
    return;
  }
  const setVisible = event => {
    isKeyboardVisible = keyboardIsOpen(event.endCoordinates?.height);
  };
  const setHidden = () => {
    isKeyboardVisible = false;
  };

  // Seed from the current keyboard metrics in case it is already open when the
  // first ScrollView mounts (mirrors ScrollView seeding from Keyboard.metrics()).
  isKeyboardVisible = keyboardIsOpen(Keyboard.metrics?.()?.height);
  keyboardTrackerSubscriptions = [Keyboard.addListener('keyboardDidShow', setVisible), Keyboard.addListener('keyboardWillShow', setVisible), Keyboard.addListener('keyboardDidHide', setHidden)];
}
function unsubscribeFromKeyboardVisibility() {
  keyboardTrackerRefCount--;
  if (keyboardTrackerRefCount > 0) {
    return;
  }
  for (const subscription of keyboardTrackerSubscriptions) {
    subscription.remove();
  }
  keyboardTrackerSubscriptions = [];
  isKeyboardVisible = false;
}
export const JSResponderContext = /*#__PURE__*/React.createContext(null);
export function updateResponderEventValue(jsResponderContext, value) {
  const responderEventRef = jsResponderContext?.isRNGHResponderEvent;
  if (responderEventRef) {
    responderEventRef.current = value;
  }
}
export function isKeyboardDismissingTap(jsResponderContext) {
  if (jsResponderContext == null) {
    return false;
  }
  const mode = jsResponderContext.keyboardShouldPersistTaps;
  const keyboardNeverPersistTaps = !mode || mode === 'never';
  return keyboardNeverPersistTaps && isKeyboardVisible;
}
const ScrollViewResponderInterceptor = ({
  children,
  keyboardShouldPersistTaps
}) => {
  const isRNGHResponderEvent = useRef(false);
  const contextValue = useMemo(() => ({
    isRNGHResponderEvent,
    keyboardShouldPersistTaps
  }), [isRNGHResponderEvent, keyboardShouldPersistTaps]);
  useEffect(() => {
    subscribeToKeyboardVisibility();
    return () => unsubscribeFromKeyboardVisibility();
  }, []);
  const resetRNGHResponderEvent = useCallback(() => {
    isRNGHResponderEvent.current = false;
    return false;
  }, []);
  const handleStartShouldSetResponder = useCallback(() => {
    const shouldHandleRNGHEvent = keyboardShouldPersistTaps === 'handled' && isRNGHResponderEvent.current;
    isRNGHResponderEvent.current = false;
    return shouldHandleRNGHEvent;
  }, [keyboardShouldPersistTaps]);

  // RNGH tap responders need to let RN components higher in the tree handle
  // the JS responder event first. If no RN component claims it, this logical
  // ScrollView child consumes the marked event before ScrollView's own
  // keyboardShouldPersistTaps='handled' responder logic handles it.
  // For more information check this comment:
  // https://github.com/software-mansion/react-native-gesture-handler/pull/4158#issuecomment-4431632964
  return /*#__PURE__*/_jsx(JSResponderContext, {
    value: contextValue,
    children: /*#__PURE__*/_jsx(View, {
      collapsable: false,
      onStartShouldSetResponderCapture: resetRNGHResponderEvent,
      onStartShouldSetResponder: handleStartShouldSetResponder,
      pointerEvents: "box-none",
      style: styles.logicalResponder,
      children: children
    })
  });
};
const styles = StyleSheet.create({
  logicalResponder: {
    display: 'contents'
  }
});
export default ScrollViewResponderInterceptor;
//# sourceMappingURL=ScrollViewResponderInterceptor.js.map
import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { DashboardScreen } from './screens/DashboardScreen';
import { RevenueDetailScreen } from './screens/RevenueDetailScreen';
import { InventoryDetailScreen } from './screens/InventoryDetailScreen';

export type DashboardStackParamList = {
  DashboardMain: undefined;
  RevenueDetail: { period?: string; groupBy?: string };
  InventoryDetail: undefined;
  CustomerDetail: undefined;
  ForecastDetail: undefined;
};

const Stack = createStackNavigator<DashboardStackParamList>();

export const DashboardNavigator: React.FC = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="DashboardMain" component={DashboardScreen} />
      <Stack.Screen name="RevenueDetail" component={RevenueDetailScreen} />
      <Stack.Screen name="InventoryDetail" component={InventoryDetailScreen} />
    </Stack.Navigator>
  );
};


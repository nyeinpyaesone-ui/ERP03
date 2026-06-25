import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useTheme } from 'react-native-paper';

// Auth Screens
import { LoginScreen } from '../screens/auth/LoginScreen';
import { ForgotPasswordScreen } from '../screens/auth/ForgotPasswordScreen';

// Main Module Navigators
import { DashboardScreen } from '../screens/dashboard/DashboardScreen';
import { ContactsNavigator } from './ContactsNavigator';
import { InvoicesNavigator } from './InvoicesNavigator';
import { SearchScreen } from '../screens/search/SearchScreen';
import { AICopilotScreen } from '../screens/ai/AICopilotScreen';
import { InventoryNavigator } from './InventoryNavigator';
import { ProfileScreen } from '../screens/profile/ProfileScreen';

// Module Navigators (P2/P3)
import { MRPNavigator } from './MRPNavigator';
import { HRNavigator } from './HRNavigator';
import { POSNavigator } from './POSNavigator';
import { EcommerceNavigator } from './EcommerceNavigator';

// Store
import { useAuthStore } from '../store/authStore';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// Auth Stack
const AuthStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
  </Stack.Navigator>
);

// Main Tab Navigator with all modules
const MainTabNavigator = () => {
  const theme = useTheme();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Dashboard':
              iconName = focused ? 'view-dashboard' : 'view-dashboard-outline';
              break;
            case 'Contacts':
              iconName = focused ? 'account-group' : 'account-group-outline';
              break;
            case 'Invoices':
              iconName = focused ? 'file-document' : 'file-document-outline';
              break;
            case 'Search':
              iconName = focused ? 'magnify' : 'magnify';
              break;
            case 'AI':
              iconName = focused ? 'robot' : 'robot-outline';
              break;
            case 'Inventory':
              iconName = focused ? 'package-variant' : 'package-variant-closed';
              break;
            case 'Manufacturing':
              iconName = focused ? 'factory' : 'factory';
              break;
            case 'HR':
              iconName = focused ? 'account-tie' : 'account-tie-outline';
              break;
            case 'POS':
              iconName = focused ? 'cart' : 'cart-outline';
              break;
            case 'Store':
              iconName = focused ? 'store' : 'store-outline';
              break;
            case 'Profile':
              iconName = focused ? 'account-circle' : 'account-circle-outline';
              break;
            default:
              iconName = 'help-circle';
          }

          return <MaterialCommunityIcons name={iconName as any} size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.onSurfaceDisabled,
        tabBarStyle: {
          elevation: 8,
          shadowColor: '#000',
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.1,
          shadowRadius: 4,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontFamily: theme.fonts.regular.fontFamily,
        },
        headerShown: false,
      })}
    >
      {/* Core v2.5 Modules */}
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ tabBarLabel: 'Home' }}
      />
      <Tab.Screen
        name="Contacts"
        component={ContactsNavigator}
        options={{ tabBarLabel: 'Contacts' }}
      />
      <Tab.Screen
        name="Invoices"
        component={InvoicesNavigator}
        options={{ tabBarLabel: 'Invoices' }}
      />
      <Tab.Screen
        name="Search"
        component={SearchScreen}
        options={{ tabBarLabel: 'Search' }}
      />
      <Tab.Screen
        name="AI"
        component={AICopilotScreen}
        options={{ tabBarLabel: 'AI' }}
      />
      <Tab.Screen
        name="Inventory"
        component={InventoryNavigator}
        options={{ tabBarLabel: 'Stock' }}
      />

      {/* P3 Modules */}
      <Tab.Screen
        name="Manufacturing"
        component={MRPNavigator}
        options={{ tabBarLabel: 'Mfg' }}
      />
      <Tab.Screen
        name="HR"
        component={HRNavigator}
        options={{ tabBarLabel: 'HR' }}
      />
      <Tab.Screen
        name="POS"
        component={POSNavigator}
        options={{ tabBarLabel: 'POS' }}
      />
      <Tab.Screen
        name="Store"
        component={EcommerceNavigator}
        options={{ tabBarLabel: 'Shop' }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ tabBarLabel: 'Me' }}
      />
    </Tab.Navigator>
  );
};

// Root Navigator with Auth Gate
export const RootNavigator: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    // Return loading screen or splash
    return null;
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <Stack.Screen name="Main" component={MainTabNavigator} />
      ) : (
        <Stack.Screen name="Auth" component={AuthStack} />
      )}
    </Stack.Navigator>
  );
};


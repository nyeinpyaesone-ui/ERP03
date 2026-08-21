import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import { POSScreen } from '../screens/pos/POSScreen';
import { ShiftManagementScreen } from '../screens/pos/ShiftManagementScreen';
import { POSReportsScreen } from '../screens/pos/POSReportsScreen';

const POSTab = createBottomTabNavigator();
const POSStack = createStackNavigator();

export const POSNavigator: React.FC = () => {
  return (
    <POSTab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;
          switch (route.name) {
            case 'POSMain':
              iconName = 'cart';
              break;
            case 'Shift':
              iconName = 'store';
              break;
            case 'Reports':
              iconName = 'chart-bar';
              break;
            default:
              iconName = 'help';
          }
          return (
            <MaterialCommunityIcons
              name={iconName as any}
              size={size}
              color={color}
            />
          );
        },
        tabBarActiveTintColor: '#6200ee',
        tabBarInactiveTintColor: 'gray',
      })}
    >
      <POSTab.Screen
        name="POSMain"
        component={POSScreen}
        options={{ title: 'Sell', headerShown: false }}
      />
      <POSTab.Screen
        name="Shift"
        component={ShiftManagementScreen}
        options={{ title: 'Shift', headerShown: false }}
      />
      <POSTab.Screen
        name="Reports"
        component={POSReportsScreen}
        options={{ title: 'Reports', headerShown: false }}
      />
    </POSTab.Navigator>
  );
};


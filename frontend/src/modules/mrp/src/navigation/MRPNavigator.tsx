// Add to your existing navigation structure

import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { MaterialCommunityIcons } from '@expo/vector-icons';

// MRP Screens
import { MRPDashboardScreen } from '../screens/mrp/MRPDashboardScreen';
import { BOMListScreen } from '../screens/mrp/BOMListScreen';
import { WorkOrdersScreen } from '../screens/mrp/WorkOrdersScreen';
import { ProductionPlanningScreen } from '../screens/mrp/ProductionPlanningScreen';
import { MRPCalculationScreen } from '../screens/mrp/MRPCalculationScreen';

const MRPStack = createStackNavigator();
const MRPTab = createBottomTabNavigator();

export const MRPNavigator: React.FC = () => {
  return (
    <MRPTab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;
          switch (route.name) {
            case 'MRPDashboard':
              iconName = 'view-dashboard';
              break;
            case 'BOMs':
              iconName = 'file-document-outline';
              break;
            case 'WorkOrders':
              iconName = 'clipboard-list';
              break;
            case 'Planning':
              iconName = 'calendar-check';
              break;
            case 'MRP':
              iconName = 'calculator';
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
      <MRPTab.Screen
        name="MRPDashboard"
        component={MRPDashboardScreen}
        options={{ title: 'Dashboard', headerShown: false }}
      />
      <MRPTab.Screen
        name="BOMs"
        component={BOMListScreen}
        options={{ title: 'BOMs', headerShown: false }}
      />
      <MRPTab.Screen
        name="WorkOrders"
        component={WorkOrdersScreen}
        options={{ title: 'Orders', headerShown: false }}
      />
      <MRPTab.Screen
        name="Planning"
        component={ProductionPlanningScreen}
        options={{ title: 'Planning', headerShown: false }}
      />
      <MRPTab.Screen
        name="MRP"
        component={MRPCalculationScreen}
        options={{ title: 'MRP', headerShown: false }}
      />
    </MRPTab.Navigator>
  );
};

// Add to your main Bottom Tab Navigator:
// <Tab.Screen name="Manufacturing" component={MRPNavigator} />


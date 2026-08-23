import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import { ProductCatalogScreen } from '../screens/ecommerce/ProductCatalogScreen';
import { ProductDetailScreen } from '../screens/ecommerce/ProductDetailScreen';
import { CartScreen } from '../screens/ecommerce/CartScreen';
import { CheckoutScreen } from '../screens/ecommerce/CheckoutScreen';
import { OrdersScreen } from '../screens/ecommerce/OrdersScreen';
import { EcommerceDashboardScreen } from '../screens/ecommerce/EcommerceDashboardScreen';

const EcommerceTab = createBottomTabNavigator();
const EcommerceStack = createStackNavigator();

const ShopStack = () => (
  <EcommerceStack.Navigator screenOptions={{ headerShown: false }}>
    <EcommerceStack.Screen name="ProductCatalog" component={ProductCatalogScreen} />
    <EcommerceStack.Screen name="ProductDetail" component={ProductDetailScreen} />
    <EcommerceStack.Screen name="Cart" component={CartScreen} />
    <EcommerceStack.Screen name="Checkout" component={CheckoutScreen} />
  </EcommerceStack.Navigator>
);

const OrderStack = () => (
  <EcommerceStack.Navigator screenOptions={{ headerShown: false }}>
    <EcommerceStack.Screen name="OrdersList" component={OrdersScreen} />
    <EcommerceStack.Screen name="OrderDetail" component={OrdersScreen} />
  </EcommerceStack.Navigator>
);

export const EcommerceNavigator: React.FC = () => {
  return (
    <EcommerceTab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;
          switch (route.name) {
            case 'Shop':
              iconName = 'store';
              break;
            case 'Cart':
              iconName = 'cart';
              break;
            case 'Orders':
              iconName = 'receipt';
              break;
            case 'Dashboard':
              iconName = 'view-dashboard';
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
      <EcommerceTab.Screen
        name="Shop"
        component={ShopStack}
        options={{ title: 'Shop', headerShown: false }}
      />
      <EcommerceTab.Screen
        name="Cart"
        component={CartScreen}
        options={{ title: 'Cart', headerShown: false }}
      />
      <EcommerceTab.Screen
        name="Orders"
        component={OrderStack}
        options={{ title: 'Orders', headerShown: false }}
      />
      <EcommerceTab.Screen
        name="Dashboard"
        component={EcommerceDashboardScreen}
        options={{ title: 'Dashboard', headerShown: false }}
      />
    </EcommerceTab.Navigator>
  );
};


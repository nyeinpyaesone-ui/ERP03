import React, { useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Text, TextInput, Button, useTheme, Card, Avatar } from 'react-native-paper';
import { useAuthStore } from '../store/authStore';

export default function LoginScreen() {
  const theme = useTheme();
  const { login, isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [secureText, setSecureText] = useState(true);

  const handleLogin = async () => {
    if (!email || !password) return;
    await login(email, password);
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.logoContainer}>
          <Avatar.Text
            size={80}
            label="AI"
            style={{ backgroundColor: theme.colors.primary }}
            labelStyle={{ color: '#fff', fontSize: 32, fontWeight: '700' }}
          />
          <Text variant="headlineMedium" style={{ fontWeight: '700', marginTop: 16 }}>
            ERP SOLUTION
          </Text>
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
            Mobile v2.5
          </Text>
        </View>

        <Card style={styles.formCard}>
          <Card.Content style={styles.formContent}>
            <Text variant="titleLarge" style={{ fontWeight: '600', marginBottom: 24 }}>
              Sign In
            </Text>

            <TextInput
              label="Email"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              mode="outlined"
              style={styles.input}
              left={<TextInput.Icon icon="email" />}
            />

            <TextInput
              label="Password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={secureText}
              mode="outlined"
              style={styles.input}
              left={<TextInput.Icon icon="lock" />}
              right={
                <TextInput.Icon
                  icon={secureText ? 'eye-off' : 'eye'}
                  onPress={() => setSecureText(!secureText)}
                />
              }
            />

            <Button
              mode="contained"
              onPress={handleLogin}
              loading={isLoading}
              disabled={isLoading || !email || !password}
              style={[styles.loginButton, { backgroundColor: theme.colors.primary }]}
              labelStyle={{ fontSize: 16, fontWeight: '600' }}
            >
              Sign In
            </Button>

            <Button
              mode="text"
              onPress={() => {}}
              style={{ marginTop: 8 }}
              labelStyle={{ fontSize: 12 }}
            >
              Forgot Password?
            </Button>
          </Card.Content>
        </Card>

        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 24, textAlign: 'center' }}>
          By signing in, you agree to our Terms of Service and Privacy Policy
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  formCard: {
    elevation: 4,
  },
  formContent: {
    padding: 8,
  },
  input: {
    marginBottom: 16,
  },
  loginButton: {
    marginTop: 8,
    paddingVertical: 6,
  },
});


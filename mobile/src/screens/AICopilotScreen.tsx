import React, { useState, useRef, useEffect } from 'react';
import { View, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { Text, TextInput, IconButton, useTheme, Card, Avatar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

const SUGGESTIONS = [
  'Show me overdue invoices',
  'Generate a sales report for Q2',
  'Find contacts in the tech industry',
  'What is the revenue trend?',
];

export default function AICopilotScreen() {
  const theme = useTheme();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your AI Copilot. I can help you with contacts, invoices, reports, and more. What would you like to do today?',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (flatListRef.current && messages.length > 0) {
      flatListRef.current.scrollToEnd({ animated: true });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const responses: Record<string, string> = {
        'Show me overdue invoices': 'I found 3 overdue invoices:\n\n1. INV-2024-142 - Acme Corp - 850,000 MMK (14 days overdue)\n2. INV-2024-138 - Startup.io - 320,000 MMK (21 days overdue)\n3. INV-2024-135 - TechLabs - 1,200,000 MMK (30 days overdue)\n\nWould you like me to send reminder emails?',
        'Generate a sales report for Q2': 'Q2 2024 Sales Report:\n\n• Total Revenue: 3,200,000 MMK (+12.5% vs Q1)\n• New Customers: 47\n• Average Deal Size: 820,000 MMK\n• Top Product: ERP Pro License\n• Best Region: Yangon (62%)\n\nI can export this as PDF or Excel.',
        'Find contacts in the tech industry': 'I found 234 contacts in the tech industry:\n\n• Enterprise: 89\n• Startups: 112\n• SaaS: 67\n• Fintech: 34\n\nTop companies: Acme Corp, TechLabs, CloudNine',
        'What is the revenue trend?': 'Revenue is trending upward with 12.5% MoM growth.\n\nKey drivers:\n• Enterprise renewals (+18%)\n• New SaaS subscriptions (+24%)\n• Professional services (+8%)\n\nForecast for next month: 4,200,000 MMK (+15%)',
      };

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responses[input.trim()] || `I understand you asked about "${input.trim()}". Let me help you with that. I can search through your ERP data, generate reports, or provide insights.`,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, aiMsg]);
      setIsLoading(false);
    }, 1500);
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={[styles.messageRow, item.role === 'user' ? styles.userRow : styles.aiRow]}>
      {item.role === 'assistant' && (
        <Avatar.Icon
          size={32}
          icon="robot"
          style={{ backgroundColor: theme.colors.secondaryContainer }}
          color={theme.colors.secondary}
        />
      )}
      <Card
        style={[
          styles.messageCard,
          {
            backgroundColor: item.role === 'user' ? theme.colors.primaryContainer : theme.colors.surfaceVariant,
          },
        ]}
      >
        <Card.Content style={{ padding: 10 }}>
          <Text variant="bodyMedium" style={{ lineHeight: 20 }}>
            {item.content}
          </Text>
        </Card.Content>
      </Card>
      {item.role === 'user' && (
        <Avatar.Text
          size={32}
          label="U"
          style={{ backgroundColor: theme.colors.primaryContainer }}
          labelStyle={{ color: theme.colors.primary }}
        />
      )}
    </View>
  );

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      {/* Header */}
      <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
        <View style={styles.headerContent}>
          <Avatar.Icon
            size={36}
            icon="robot"
            style={{ backgroundColor: theme.colors.secondaryContainer }}
            color={theme.colors.secondary}
          />
          <View style={{ marginLeft: 12 }}>
            <Text variant="titleMedium" style={{ fontWeight: '600' }}>AI Copilot</Text>
            <View style={styles.onlineIndicator}>
              <View style={[styles.dot, { backgroundColor: '#10B981' }]} />
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>Online</Text>
            </View>
          </View>
        </View>
      </View>

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.messageList}
        showsVerticalScrollIndicator={false}
      />

      {/* Suggestions */}
      {messages.length === 1 && (
        <View style={styles.suggestionsContainer}>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}>
            Try asking:
          </Text>
          <View style={styles.suggestionsRow}>
            {SUGGESTIONS.map((suggestion, i) => (
              <IconButton
                key={i}
                icon="lightning-bolt"
                mode="contained-tonal"
                size={14}
                style={styles.suggestionButton}
                onPress={() => {
                  setInput(suggestion);
                  sendMessage();
                }}
              >
                <Text variant="bodySmall">{suggestion}</Text>
              </IconButton>
            ))}
          </View>
        </View>
      )}

      {/* Input */}
      <View style={[styles.inputContainer, { backgroundColor: theme.colors.surface }]}>
        <TextInput
          mode="flat"
          placeholder="Ask AI Copilot..."
          value={input}
          onChangeText={setInput}
          style={styles.input}
          multiline
          maxLength={500}
          right={
            <TextInput.Icon
              icon={isLoading ? 'loading' : 'send'}
              onPress={sendMessage}
              color={input.trim() ? theme.colors.primary : theme.colors.onSurfaceVariant}
            />
          }
        />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 16,
    paddingTop: 24,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  onlineIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  messageList: {
    padding: 16,
  },
  messageRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginBottom: 12,
    maxWidth: '90%',
  },
  userRow: {
    alignSelf: 'flex-end',
  },
  aiRow: {
    alignSelf: 'flex-start',
  },
  messageCard: {
    marginHorizontal: 8,
    maxWidth: '80%',
  },
  suggestionsContainer: {
    padding: 16,
    paddingTop: 0,
  },
  suggestionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  suggestionButton: {
    margin: 0,
  },
  inputContainer: {
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  input: {
    backgroundColor: 'transparent',
    maxHeight: 100,
  },
});


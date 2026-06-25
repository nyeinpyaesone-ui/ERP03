import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { Text, Card } from 'react-native-paper';
import { BarChart } from 'react-native-chart-kit';
import { ChartData } from '../types/dashboard';

interface BarChartCardProps {
  title: string;
  subtitle?: string;
  data: ChartData | null;
  loading: boolean;
  height?: number;
}

export const BarChartCard: React.FC<BarChartCardProps> = ({
  title,
  subtitle,
  data,
  loading,
  height = 220,
}) => {
  if (loading || !data) {
    return (
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.skeletonHeader}>
            <View style={{ height: 20, backgroundColor: '#E0E0E0', borderRadius: 4, width: '40%' }} />
          </View>
          <View style={[styles.skeletonChart, { height }]} />
        </Card.Content>
      </Card>
    );
  }

  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map(ds => ({
      data: ds.data,
    })),
  };

  const screenWidth = Dimensions.get('window').width - 48;

  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.title}>{title}</Text>
        {subtitle && <Text variant="bodySmall" style={styles.subtitle}>{subtitle}</Text>}
        <BarChart
          data={chartData}
          width={screenWidth}
          height={height}
          chartConfig={{
            backgroundColor: '#fff',
            backgroundGradientFrom: '#fff',
            backgroundGradientTo: '#fff',
            decimalPlaces: 0,
            color: (opacity = 1) => `rgba(25, 118, 210, ${opacity})`,
            labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
            style: {
              borderRadius: 8,
            },
            propsForLabels: {
              fontSize: 10,
            },
            barPercentage: 0.7,
          }}
          style={styles.chart}
          fromZero
          showValuesOnTopOfBars
        />
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    margin: 8,
  },
  title: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    color: '#666',
    marginBottom: 12,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 8,
  },
  skeletonHeader: {
    marginBottom: 12,
  },
  skeletonChart: {
    backgroundColor: '#E0E0E0',
    borderRadius: 8,
  },
});


import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { Text, Card } from 'react-native-paper';
import { PieChart } from 'react-native-chart-kit';

interface PieChartCardProps {
  title: string;
  data: Array<{
    name: string;
    value: number;
    color: string;
    legendFontColor?: string;
    legendFontSize?: number;
  }>;
  loading: boolean;
  height?: number;
}

export const PieChartCard: React.FC<PieChartCardProps> = ({
  title,
  data,
  loading,
  height = 200,
}) => {
  if (loading || !data.length) {
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

  const chartData = data.map(item => ({
    name: item.name,
    population: item.value,
    color: item.color,
    legendFontColor: item.legendFontColor || '#666',
    legendFontSize: item.legendFontSize || 12,
  }));

  const screenWidth = Dimensions.get('window').width - 48;

  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.title}>{title}</Text>
        <PieChart
          data={chartData}
          width={screenWidth}
          height={height}
          chartConfig={{
            color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
          }}
          accessor="population"
          backgroundColor="transparent"
          paddingLeft="15"
          style={styles.chart}
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
  chart: {
    marginVertical: 8,
  },
  skeletonHeader: {
    marginBottom: 12,
  },
  skeletonChart: {
    backgroundColor: '#E0E0E0',
    borderRadius: 8,
  },
});


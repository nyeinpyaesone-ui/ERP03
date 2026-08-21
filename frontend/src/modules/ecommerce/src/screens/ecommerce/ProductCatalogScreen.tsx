import React from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity, ScrollView, Image } from 'react-native';
import { Card, Text, Searchbar, Chip, FAB, useTheme, IconButton, Badge, Button } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ecommerceProductAPI, ecommerceCategoryAPI } from '../../services/api/ecommerceApi';
import { useEcommerceStore } from '../../store/ecommerceStore';
import { StoreProduct, StoreCategory, SearchFilters } from '../../types/ecommerce';

export const ProductCatalogScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigation = useNavigation();
  const {
    searchQuery,
    setSearchQuery,
    searchFilters,
    setSearchFilters,
    selectedCategory,
    setSelectedCategory,
    cart,
    wishlist,
    addToWishlist,
    removeFromWishlist,
    isInWishlist,
  } = useEcommerceStore();

  const [page, setPage] = React.useState(1);
  const [showFilters, setShowFilters] = React.useState(false);

  const { data: categories } = useQuery<StoreCategory[]>({
    queryKey: ['storeCategories'],
    queryFn: () => ecommerceCategoryAPI.getAll(),
  });

  const { data: productsData, isLoading } = useQuery({
    queryKey: ['storeProducts', selectedCategory?.id, searchQuery, searchFilters, page],
    queryFn: () =>
      ecommerceProductAPI.getAll({
        category: selectedCategory?.id,
        search: searchQuery || undefined,
        page,
        limit: 20,
      }),
  });

  const { data: featuredProducts } = useQuery({
    queryKey: ['featuredProducts'],
    queryFn: () => ecommerceProductAPI.getAll({ featured: true, limit: 6 }),
  });

  const { data: newProducts } = useQuery({
    queryKey: ['newProducts'],
    queryFn: () => ecommerceProductAPI.getAll({ new: true, limit: 6 }),
  });

  const handleProductPress = (product: StoreProduct) => {
    setSelectedCategory(null);
    navigation.navigate('ProductDetail', { slug: product.slug } as never);
  };

  const handleCategoryPress = (category: StoreCategory) => {
    setSelectedCategory(category);
    setSearchQuery('');
    setPage(1);
  };

  const toggleWishlist = (product: StoreProduct) => {
    if (isInWishlist(product.id)) {
      const item = wishlist.find((w) => w.productId === product.id);
      if (item) removeFromWishlist(item.id);
    } else {
      addToWishlist({
        id: `wish-${Date.now()}`,
        productId: product.id,
        productName: product.name,
        productSlug: product.slug,
        productImage: product.images.find((i) => i.isPrimary)?.url || product.images[0]?.url || '',
        unitPrice: product.price,
        addedAt: new Date().toISOString(),
      });
    }
  };

  const renderProductCard = ({ item }: { item: StoreProduct }) => {
    const primaryImage = item.images.find((i) => i.isPrimary)?.url || item.images[0]?.url;
    const discount = item.compareAtPrice ? Math.round(((item.compareAtPrice - item.price) / item.compareAtPrice) * 100) : 0;
    const isWishlisted = isInWishlist(item.id);

    return (
      <TouchableOpacity
        onPress={() => handleProductPress(item)}
        style={styles.productCardContainer}
      >
        <Card style={styles.productCard}>
          <View style={styles.imageContainer}>
            {primaryImage ? (
              <Image source={{ uri: primaryImage }} style={styles.productImage} />
            ) : (
              <View style={[styles.productImage, styles.imagePlaceholder]}>
                <MaterialCommunityIcons name="package-variant" size={40} color={theme.colors.primary} />
              </View>
            )}
            {discount > 0 && (
              <View style={styles.discountBadge}>
                <Text variant="bodySmall" style={styles.discountText}>
                  -{discount}%
                </Text>
              </View>
            )}
            {item.isNew && (
              <View style={[styles.badge, { backgroundColor: '#4caf50' }]}>
                <Text variant="bodySmall" style={styles.badgeText}>
                  NEW
                </Text>
              </View>
            )}
            <IconButton
              icon={isWishlisted ? 'heart' : 'heart-outline'}
              size={20}
              iconColor={isWishlisted ? '#f44336' : '#fff'}
              style={styles.wishlistButton}
              onPress={() => toggleWishlist(item)}
            />
          </View>
          <Card.Content style={styles.cardContent}>
            <Text variant="bodySmall" style={styles.categoryName} numberOfLines={1}>
              {item.categoryName}
            </Text>
            <Text variant="titleSmall" style={styles.productName} numberOfLines={2}>
              {item.name}
            </Text>
            <View style={styles.priceRow}>
              <Text variant="titleMedium" style={styles.price}>
                {item.price.toLocaleString()} MMK
              </Text>
              {item.compareAtPrice && (
                <Text variant="bodySmall" style={styles.comparePrice}>
                  {item.compareAtPrice.toLocaleString()} MMK
                </Text>
              )}
            </View>
            <View style={styles.ratingRow}>
              <MaterialCommunityIcons name="star" size={14} color="#ffc107" />
              <Text variant="bodySmall" style={styles.ratingText}>
                {item.rating} ({item.reviewCount})
              </Text>
            </View>
            {item.stockStatus === 'out_of_stock' && (
              <Text variant="bodySmall" style={{ color: theme.colors.error, marginTop: 4 }}>
                Out of Stock
              </Text>
            )}
            {item.stockStatus === 'pre_order' && (
              <Text variant="bodySmall" style={{ color: '#ff9800', marginTop: 4 }}>
                Pre-order
              </Text>
            )}
          </Card.Content>
        </Card>
      </TouchableOpacity>
    );
  };

  const renderHorizontalProduct = ({ item }: { item: StoreProduct }) => (
    <TouchableOpacity
      onPress={() => handleProductPress(item)}
      style={styles.horizontalCardContainer}
    >
      <Card style={styles.horizontalCard}>
        <View style={styles.horizontalImageContainer}>
          {item.images[0]?.url ? (
            <Image source={{ uri: item.images[0].url }} style={styles.horizontalImage} />
          ) : (
            <View style={[styles.horizontalImage, styles.imagePlaceholder]}>
              <MaterialCommunityIcons name="package-variant" size={30} color={theme.colors.primary} />
            </View>
          )}
        </View>
        <Card.Content style={styles.horizontalContent}>
          <Text variant="bodySmall" style={styles.productName} numberOfLines={2}>
            {item.name}
          </Text>
          <Text variant="titleSmall" style={styles.price}>
            {item.price.toLocaleString()} MMK
          </Text>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Searchbar
          placeholder="Search products..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchbar}
          onSubmitEditing={() => {
            setSelectedCategory(null);
            setPage(1);
          }}
        />
        <IconButton
          icon="filter-variant"
          size={24}
          onPress={() => setShowFilters(!showFilters)}
          style={styles.filterButton}
        />
      </View>

      {showFilters && (
        <View style={styles.filtersContainer}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filtersContent}>
            <Chip
              selected={searchFilters.sortBy === 'price_asc'}
              onPress={() => setSearchFilters({ sortBy: 'price_asc' })}
              style={styles.filterChip}
            >
              Price: Low to High
            </Chip>
            <Chip
              selected={searchFilters.sortBy === 'price_desc'}
              onPress={() => setSearchFilters({ sortBy: 'price_desc' })}
              style={styles.filterChip}
            >
              Price: High to Low
            </Chip>
            <Chip
              selected={searchFilters.sortBy === 'bestselling'}
              onPress={() => setSearchFilters({ sortBy: 'bestselling' })}
              style={styles.filterChip}
            >
              Bestselling
            </Chip>
            <Chip
              selected={searchFilters.sortBy === 'rating'}
              onPress={() => setSearchFilters({ sortBy: 'rating' })}
              style={styles.filterChip}
            >
              Top Rated
            </Chip>
            <Chip
              selected={searchFilters.inStock}
              onPress={() => setSearchFilters({ inStock: !searchFilters.inStock })}
              style={styles.filterChip}
            >
              In Stock Only
            </Chip>
          </ScrollView>
        </View>
      )}

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {/* Categories */}
        {!selectedCategory && !searchQuery && (
          <View style={styles.section}>
            <Text variant="titleMedium" style={styles.sectionTitle}>
              Categories
            </Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.categoriesScroll}
            >
              {categories?.map((category) => (
                <TouchableOpacity
                  key={category.id}
                  onPress={() => handleCategoryPress(category)}
                  style={styles.categoryCard}
                >
                  <Card>
                    <Card.Content style={styles.categoryContent}>
                      {category.imageUrl ? (
                        <Image source={{ uri: category.imageUrl }} style={styles.categoryImage} />
                      ) : (
                        <View style={[styles.categoryImage, styles.imagePlaceholder]}>
                          <MaterialCommunityIcons name="folder" size={30} color={theme.colors.primary} />
                        </View>
                      )}
                      <Text variant="bodySmall" style={styles.categoryName} numberOfLines={2}>
                        {category.name}
                      </Text>
                      <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                        {category.productCount} items
                      </Text>
                    </Card.Content>
                  </Card>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Selected Category Header */}
        {selectedCategory && (
          <View style={styles.categoryHeader}>
            <Button
              icon="arrow-left"
              mode="text"
              onPress={() => setSelectedCategory(null)}
              style={styles.backButton}
            >
              All Categories
            </Button>
            <Text variant="titleMedium" style={styles.categoryTitle}>
              {selectedCategory.name}
            </Text>
            <Text variant="bodySmall" style={{ opacity: 0.6 }}>
              {selectedCategory.productCount} products
            </Text>
          </View>
        )}

        {/* Featured Products */}
        {!selectedCategory && !searchQuery && featuredProducts?.products && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text variant="titleMedium" style={styles.sectionTitle}>
                Featured Products
              </Text>
              <Button mode="text" compact onPress={() => {}}>
                See All
              </Button>
            </View>
            <FlatList
              data={featuredProducts.products}
              renderItem={renderHorizontalProduct}
              keyExtractor={(item) => `featured-${item.id}`}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalList}
            />
          </View>
        )}

        {/* New Products */}
        {!selectedCategory && !searchQuery && newProducts?.products && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text variant="titleMedium" style={styles.sectionTitle}>
                New Arrivals
              </Text>
              <Button mode="text" compact onPress={() => {}}>
                See All
              </Button>
            </View>
            <FlatList
              data={newProducts.products}
              renderItem={renderHorizontalProduct}
              keyExtractor={(item) => `new-${item.id}`}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.horizontalList}
            />
          </View>
        )}

        {/* Product Grid */}
        <View style={styles.section}>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            {searchQuery ? `Search: "${searchQuery}"` : selectedCategory ? 'Products' : 'All Products'}
          </Text>
          <FlatList
            data={productsData?.products}
            renderItem={renderProductCard}
            keyExtractor={(item) => item.id}
            numColumns={2}
            scrollEnabled={false}
            contentContainerStyle={styles.productGrid}
            ListEmptyComponent={
              <View style={styles.emptyState}>
                <MaterialCommunityIcons name="package-variant" size={64} color={theme.colors.outline} />
                <Text variant="bodyLarge" style={{ opacity: 0.5, marginTop: 16 }}>
                  No products found
                </Text>
              </View>
            }
          />
          {productsData && productsData.page < productsData.totalPages && (
            <Button
              mode="outlined"
              onPress={() => setPage(page + 1)}
              style={styles.loadMoreButton}
              loading={isLoading}
            >
              Load More
            </Button>
          )}
        </View>
      </ScrollView>

      {/* Cart FAB */}
      {cart && cart.itemCount > 0 && (
        <FAB
          icon="cart"
          style={[styles.fab, { backgroundColor: theme.colors.primary }]}
          onPress={() => navigation.navigate('Cart' as never)}
          label={`${cart.itemCount} items`}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    paddingBottom: 8,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  searchbar: {
    flex: 1,
    marginRight: 8,
  },
  filterButton: {
    margin: 0,
  },
  filtersContainer: {
    backgroundColor: '#fff',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  filtersContent: {
    paddingHorizontal: 12,
    gap: 8,
  },
  filterChip: {
    marginRight: 8,
  },
  scrollContent: {
    paddingBottom: 80,
  },
  section: {
    marginTop: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  sectionTitle: {
    fontWeight: 'bold',
  },
  categoriesScroll: {
    paddingHorizontal: 12,
    gap: 12,
  },
  categoryCard: {
    width: 120,
    marginRight: 12,
  },
  categoryContent: {
    alignItems: 'center',
    padding: 12,
  },
  categoryImage: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginBottom: 8,
  },
  categoryName: {
    textAlign: 'center',
    fontWeight: '500',
  },
  categoryHeader: {
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    alignSelf: 'flex-start',
    marginLeft: -8,
    marginBottom: 8,
  },
  categoryTitle: {
    fontWeight: 'bold',
  },
  horizontalList: {
    paddingHorizontal: 12,
  },
  horizontalCardContainer: {
    width: 160,
    marginRight: 12,
  },
  horizontalCard: {
    height: 220,
  },
  horizontalImageContainer: {
    height: 120,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    overflow: 'hidden',
  },
  horizontalImage: {
    width: '100%',
    height: '100%',
  },
  horizontalContent: {
    padding: 12,
  },
  productGrid: {
    padding: 12,
    gap: 12,
  },
  productCardContainer: {
    flex: 1,
    maxWidth: '50%',
    padding: 6,
  },
  productCard: {
    overflow: 'hidden',
  },
  imageContainer: {
    height: 180,
    position: 'relative',
    backgroundColor: '#f0f0f0',
  },
  productImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  imagePlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  discountBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: '#f44336',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  discountText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  wishlistButton: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  cardContent: {
    padding: 12,
  },
  productName: {
    fontWeight: '500',
    marginTop: 4,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    gap: 8,
  },
  price: {
    fontWeight: 'bold',
    color: '#6200ee',
  },
  comparePrice: {
    textDecorationLine: 'line-through',
    opacity: 0.6,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 4,
  },
  ratingText: {
    opacity: 0.7,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
  },
  loadMoreButton: {
    margin: 16,
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});


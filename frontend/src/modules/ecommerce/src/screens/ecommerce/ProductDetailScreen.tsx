import React from 'react';
import { View, StyleSheet, ScrollView, Image, TouchableOpacity, Dimensions } from 'react-native';
import { Card, Text, Button, Chip, IconButton, useTheme, Divider, Badge, ProgressBar } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useRoute, useNavigation } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ecommerceProductAPI, ecommerceCartAPI } from '../../services/api/ecommerceApi';
import { useEcommerceStore } from '../../store/ecommerceStore';
import { StoreProduct, ProductVariant } from '../../types/ecommerce';

const { width } = Dimensions.get('window');

export const ProductDetailScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const route = useRoute();
  const navigation = useNavigation();
  const { slug } = route.params as { slug: string };

  const {
    cart,
    setCart,
    wishlist,
    addToWishlist,
    removeFromWishlist,
    isInWishlist,
  } = useEcommerceStore();

  const [selectedImage, setSelectedImage] = React.useState(0);
  const [selectedVariant, setSelectedVariant] = React.useState<ProductVariant | null>(null);
  const [quantity, setQuantity] = React.useState(1);
  const [selectedAttributes, setSelectedAttributes] = React.useState<Record<string, string>>({});

  const { data: product } = useQuery<StoreProduct>({
    queryKey: ['product', slug],
    queryFn: () => ecommerceProductAPI.getBySlug(slug),
  });

  const { data: relatedProducts } = useQuery({
    queryKey: ['relatedProducts', product?.id],
    queryFn: () => ecommerceProductAPI.getRelated(product!.id, 4),
    enabled: !!product,
  });

  const { data: reviewsData } = useQuery({
    queryKey: ['productReviews', product?.id],
    queryFn: () => ecommerceProductAPI.getReviews(product!.id, { limit: 3 }),
    enabled: !!product,
  });

  const addToCartMutation = useMutation({
    mutationFn: () =>
      ecommerceCartAPI.addItem(cart?.sessionId || 'session-id', {
        productId: product!.id,
        variantId: selectedVariant?.id,
        quantity,
      }),
    onSuccess: (data) => {
      setCart(data);
    },
  });

  const handleAttributeSelect = (attributeName: string, value: string) => {
    const newAttributes = { ...selectedAttributes, [attributeName]: value };
    setSelectedAttributes(newAttributes);

    // Find matching variant
    if (product?.variants) {
      const matchingVariant = product.variants.find((v) =>
        Object.entries(newAttributes).every(
          ([key, val]) => v.attributeValues[key] === val
        )
      );
      setSelectedVariant(matchingVariant || null);
    }
  };

  const handleAddToCart = () => {
    if (!product) return;
    addToCartMutation.mutate();
  };

  const handleWishlistToggle = () => {
    if (!product) return;
    if (isInWishlist(product.id)) {
      const item = wishlist.find((w) => w.productId === product.id);
      if (item) removeFromWishlist(item.id);
    } else {
      addToWishlist({
        id: `wish-${Date.now()}`,
        productId: product.id,
        productName: product.name,
        productSlug: product.slug,
        productImage: product.images[0]?.url || '',
        unitPrice: selectedVariant?.price || product.price,
        addedAt: new Date().toISOString(),
      });
    }
  };

  const currentPrice = selectedVariant?.price || product?.price || 0;
  const currentComparePrice = selectedVariant?.compareAtPrice || product?.compareAtPrice;
  const currentStock = selectedVariant?.stockQuantity || product?.stockQuantity || 0;
  const currentStockStatus = selectedVariant?.stockStatus || product?.stockStatus || 'out_of_stock';
  const isWishlisted = product ? isInWishlist(product.id) : false;

  if (!product) return null;

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Image Gallery */}
        <View style={styles.imageGallery}>
          <ScrollView
            horizontal
            pagingEnabled
            showsHorizontalScrollIndicator={false}
            onScroll={(e) => {
              const page = Math.round(e.nativeEvent.contentOffset.x / width);
              setSelectedImage(page);
            }}
          >
            {product.images.map((image, index) => (
              <Image
                key={image.id}
                source={{ uri: image.url }}
                style={styles.mainImage}
                resizeMode="cover"
              />
            ))}
          </ScrollView>
          <View style={styles.imageIndicators}>
            {product.images.map((_, index) => (
              <View
                key={index}
                style={[
                  styles.indicator,
                  selectedImage === index && styles.activeIndicator,
                ]}
              />
            ))}
          </View>
          <IconButton
            icon={isWishlisted ? 'heart' : 'heart-outline'}
            size={28}
            iconColor={isWishlisted ? '#f44336' : '#fff'}
            style={styles.wishlistButton}
            onPress={handleWishlistToggle}
          />
        </View>

        {/* Product Info */}
        <Card style={styles.infoCard}>
          <Card.Content>
            <View style={styles.headerRow}>
              <View style={styles.headerLeft}>
                <Text variant="bodySmall" style={styles.categoryName}>
                  {product.categoryName}
                </Text>
                <Text variant="headlineSmall" style={styles.productName}>
                  {product.name}
                </Text>
              </View>
              <View style={styles.ratingBadge}>
                <MaterialCommunityIcons name="star" size={16} color="#ffc107" />
                <Text variant="bodySmall" style={styles.ratingText}>
                  {product.rating}
                </Text>
              </View>
            </View>

            <View style={styles.priceRow}>
              <Text variant="headlineMedium" style={styles.price}>
                {currentPrice.toLocaleString()} MMK
              </Text>
              {currentComparePrice && (
                <Text variant="titleMedium" style={styles.comparePrice}>
                  {currentComparePrice.toLocaleString()} MMK
                </Text>
              )}
              {currentComparePrice && (
                <View style={styles.discountBadge}>
                  <Text variant="bodySmall" style={styles.discountText}>
                    {Math.round(((currentComparePrice - currentPrice) / currentComparePrice) * 100)}% OFF
                  </Text>
                </View>
              )}
            </View>

            <View style={styles.stockRow}>
              <MaterialCommunityIcons
                name={currentStockStatus === 'in_stock' ? 'check-circle' : 'alert-circle'}
                size={16}
                color={currentStockStatus === 'in_stock' ? '#4caf50' : '#f44336'}
              />
              <Text variant="bodySmall" style={[
                styles.stockText,
                { color: currentStockStatus === 'in_stock' ? '#4caf50' : '#f44336' },
              ]}>
                {currentStockStatus === 'in_stock' ? `In Stock (${currentStock} available)` : 'Out of Stock'}
              </Text>
            </View>

            <Divider style={styles.divider} />

            {/* Attributes */}
            {product.attributes.map((attr) => (
              <View key={attr.id} style={styles.attributeSection}>
                <Text variant="titleSmall" style={styles.attributeName}>
                  {attr.name}
                </Text>
                <View style={styles.attributeValues}>
                  {attr.values.map((value) => (
                    <TouchableOpacity
                      key={value}
                      onPress={() => handleAttributeSelect(attr.name, value)}
                    >
                      <Chip
                        selected={selectedAttributes[attr.name] === value}
                        style={styles.attributeChip}
                        showSelectedCheck={false}
                      >
                        {value}
                      </Chip>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            ))}

            {/* Quantity */}
            <View style={styles.quantitySection}>
              <Text variant="titleSmall" style={styles.quantityLabel}>
                Quantity
              </Text>
              <View style={styles.quantityControl}>
                <IconButton
                  icon="minus"
                  size={20}
                  onPress={() => setQuantity(Math.max(1, quantity - 1))}
                  disabled={quantity <= 1}
                />
                <Text variant="titleMedium" style={styles.quantityValue}>
                  {quantity}
                </Text>
                <IconButton
                  icon="plus"
                  size={20}
                  onPress={() => setQuantity(Math.min(currentStock, quantity + 1))}
                  disabled={quantity >= currentStock}
                />
              </View>
            </View>

            <Divider style={styles.divider} />

            {/* Description */}
            <Text variant="titleSmall" style={styles.sectionTitle}>
              Description
            </Text>
            <Text variant="bodyMedium" style={styles.description}>
              {product.description}
            </Text>

            {/* Specifications */}
            {product.weight > 0 && (
              <View style={styles.specsSection}>
                <Text variant="titleSmall" style={styles.sectionTitle}>
                  Specifications
                </Text>
                <View style={styles.specRow}>
                  <Text variant="bodyMedium" style={styles.specLabel}>Weight</Text>
                  <Text variant="bodyMedium">{product.weight} {product.weightUnit}</Text>
                </View>
                {product.dimensions && (
                  <>
                    <View style={styles.specRow}>
                      <Text variant="bodyMedium" style={styles.specLabel}>Length</Text>
                      <Text variant="bodyMedium">{product.dimensions.length} {product.dimensions.unit}</Text>
                    </View>
                    <View style={styles.specRow}>
                      <Text variant="bodyMedium" style={styles.specLabel}>Width</Text>
                      <Text variant="bodyMedium">{product.dimensions.width} {product.dimensions.unit}</Text>
                    </View>
                    <View style={styles.specRow}>
                      <Text variant="bodyMedium" style={styles.specLabel}>Height</Text>
                      <Text variant="bodyMedium">{product.dimensions.height} {product.dimensions.unit}</Text>
                    </View>
                  </>
                )}
              </View>
            )}

            {/* Reviews */}
            {reviewsData && reviewsData.reviews.length > 0 && (
              <View style={styles.reviewsSection}>
                <View style={styles.reviewsHeader}>
                  <Text variant="titleSmall" style={styles.sectionTitle}>
                    Reviews ({reviewsData.total})
                  </Text>
                  <View style={styles.ratingSummary}>
                    <Text variant="headlineMedium" style={styles.averageRating}>
                      {reviewsData.averageRating}
                    </Text>
                    <MaterialCommunityIcons name="star" size={24} color="#ffc107" />
                  </View>
                </View>
                {reviewsData.reviews.map((review) => (
                  <Card key={review.id} style={styles.reviewCard}>
                    <Card.Content>
                      <View style={styles.reviewHeader}>
                        <Text variant="bodyMedium" style={styles.reviewAuthor}>
                          {review.customerName}
                        </Text>
                        <View style={styles.reviewRating}>
                          {[...Array(5)].map((_, i) => (
                            <MaterialCommunityIcons
                              key={i}
                              name={i < review.rating ? 'star' : 'star-outline'}
                              size={14}
                              color="#ffc107"
                            />
                          ))}
                        </View>
                      </View>
                      <Text variant="titleSmall" style={styles.reviewTitle}>
                        {review.title}
                      </Text>
                      <Text variant="bodyMedium" style={styles.reviewContent}>
                        {review.content}
                      </Text>
                      {review.isVerifiedPurchase && (
                        <Chip compact style={styles.verifiedBadge}>
                          Verified Purchase
                        </Chip>
                      )}
                    </Card.Content>
                  </Card>
                ))}
              </View>
            )}
          </Card.Content>
        </Card>
      </ScrollView>

      {/* Bottom Action Bar */}
      <View style={styles.bottomBar}>
        <View style={styles.bottomPrice}>
          <Text variant="bodySmall" style={{ opacity: 0.6 }}>Total</Text>
          <Text variant="titleLarge" style={styles.bottomPriceValue}>
            {(currentPrice * quantity).toLocaleString()} MMK
          </Text>
        </View>
        <Button
          mode="contained"
          onPress={handleAddToCart}
          loading={addToCartMutation.isPending}
          disabled={currentStockStatus === 'out_of_stock' || addToCartMutation.isPending}
          style={styles.addToCartButton}
          contentStyle={styles.addToCartButtonContent}
          icon="cart-plus"
        >
          {currentStockStatus === 'out_of_stock' ? 'Out of Stock' : 'Add to Cart'}
        </Button>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  imageGallery: {
    position: 'relative',
    height: 350,
    backgroundColor: '#f0f0f0',
  },
  mainImage: {
    width,
    height: 350,
  },
  imageIndicators: {
    position: 'absolute',
    bottom: 16,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  indicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255,255,255,0.5)',
  },
  activeIndicator: {
    backgroundColor: '#fff',
    width: 24,
  },
  wishlistButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  infoCard: {
    margin: 16,
    marginTop: -20,
    borderRadius: 16,
    elevation: 4,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  headerLeft: {
    flex: 1,
    marginRight: 12,
  },
  categoryName: {
    opacity: 0.6,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  productName: {
    fontWeight: 'bold',
  },
  ratingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff8e1',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    gap: 4,
  },
  ratingText: {
    fontWeight: 'bold',
    color: '#ff8f00',
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  price: {
    fontWeight: 'bold',
    color: '#6200ee',
  },
  comparePrice: {
    textDecorationLine: 'line-through',
    opacity: 0.6,
  },
  discountBadge: {
    backgroundColor: '#f44336',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  discountText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  stockRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 8,
  },
  stockText: {
    fontWeight: '500',
  },
  divider: {
    marginVertical: 16,
  },
  attributeSection: {
    marginBottom: 16,
  },
  attributeName: {
    marginBottom: 8,
  },
  attributeValues: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  attributeChip: {
    marginBottom: 4,
  },
  quantitySection: {
    marginBottom: 16,
  },
  quantityLabel: {
    marginBottom: 8,
  },
  quantityControl: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  quantityValue: {
    minWidth: 40,
    textAlign: 'center',
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  description: {
    lineHeight: 22,
    opacity: 0.8,
  },
  specsSection: {
    marginTop: 16,
  },
  specRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  specLabel: {
    opacity: 0.6,
  },
  reviewsSection: {
    marginTop: 16,
  },
  reviewsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  ratingSummary: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  averageRating: {
    fontWeight: 'bold',
    color: '#ff8f00',
  },
  reviewCard: {
    marginBottom: 12,
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  reviewAuthor: {
    fontWeight: '500',
  },
  reviewRating: {
    flexDirection: 'row',
    gap: 2,
  },
  reviewTitle: {
    fontWeight: '500',
    marginBottom: 4,
  },
  reviewContent: {
    opacity: 0.8,
    lineHeight: 20,
  },
  verifiedBadge: {
    marginTop: 8,
    alignSelf: 'flex-start',
  },
  bottomBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    gap: 16,
  },
  bottomPrice: {
    flex: 1,
  },
  bottomPriceValue: {
    fontWeight: 'bold',
    color: '#6200ee',
  },
  addToCartButton: {
    flex: 2,
  },
  addToCartButtonContent: {
    paddingVertical: 8,
  },
});

---



---


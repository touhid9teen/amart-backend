from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import Http404
from django.db.models import Q
from .models import Category, Product, UserCart
from .serializers import (
    CategorySerializer, 
    ProductListSerializer, 
    ProductDetailSerializer,
    UserCartSerializer
)
from rest_framework.pagination import PageNumberPagination

# class StandardResultsSetPagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'page_size'
#     max_page_size = 100

# Category API Views
class CategoryList(APIView):
    """
    List all categories or create a new category.
    """
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get(self, request, format=None):
        """
        Get all categories with optional filtering.
        
        Query Parameters:
        - search: Search term for name or documentId
        - has_image: Filter categories with images (true/false)
        - has_products: Filter categories with products (true/false)
        """
        categories = Category.objects.all()
        
        # Apply filters
        search = request.query_params.get('search')
        if search:
            categories = categories.filter(
                Q(name__icontains=search) | Q(documentId__icontains=search)
            )
        
        has_image = request.query_params.get('has_image')
        if has_image:
            if has_image.lower() == 'true':
                categories = categories.filter(image__isnull=False)
            elif has_image.lower() == 'false':
                categories = categories.filter(image__isnull=True)
        
        has_products = request.query_params.get('has_products')
        if has_products:
            if has_products.lower() == 'true':
                categories = categories.filter(products__isnull=False).distinct()
            elif has_products.lower() == 'false':
                categories = categories.filter(products__isnull=True)
        
        # Apply pagination
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


    def post(self, request, format=None):
        """
        Create a new category with optional image.
        
        Request Body:
        - documentId: Unique identifier for the category
        - name: Category name
        - colore: Optional color code
        - image: Optional image file or base64 encoded image
        - image_alt: Optional alt text for the image
        """
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryDetail(APIView):
    """
    Retrieve, update or delete a category instance.
    """
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Get a specific category by ID.
        """
        category = self.get_object(pk)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a category with optional image update.
        
        Request Body:
        - documentId: Unique identifier for the category
        - name: Category name
        - colore: Optional color code
        - image: Optional image file or base64 encoded image
        - image_alt: Optional alt text for the image
        """
        category = self.get_object(pk)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a category and its associated image.
        """
        category = self.get_object(pk)
        category.delete()  # This will also delete the image file
        return Response(status=status.HTTP_204_NO_CONTENT)

# Product API Views
class ProductList(APIView):
    """
    List all products or create a new product.
    """
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get(self, request, format=None):
        """
        Get all products with optional filtering.
        
        Query Parameters:
        - search: Search term for name or description
        - category_id: Filter by category ID
        - category_slug: Filter by category slug
        - is_featured: Filter featured products (true/false)
        - min_price: Filter by minimum selling price
        - max_price: Filter by maximum selling price
        - has_image: Filter products with images (true/false)
        """
        products = Product.objects.filter(is_active=True)
        
        # Apply filters
        search = request.query_params.get('search')
        if search:
            products = products.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        category_id = request.query_params.get('category_id')
        if category_id:
            products = products.filter(categories__id=category_id)
        
        category_slug = request.query_params.get('category_slug')
        if category_slug:
            products = products.filter(categories__slug=category_slug)
        
        is_featured = request.query_params.get('is_featured')
        if is_featured:
            if is_featured.lower() == 'true':
                products = products.filter(is_featured=True)
        
        min_price = request.query_params.get('min_price')
        if min_price:
            products = products.filter(sellingPice__gte=min_price)
        
        max_price = request.query_params.get('max_price')
        if max_price:
            products = products.filter(sellingPice__lte=max_price)
        
        has_image = request.query_params.get('has_image')
        if has_image:
            if has_image.lower() == 'true':
                products = products.filter(image__isnull=False)
            elif has_image.lower() == 'false':
                products = products.filter(image__isnull=True)
        
        # Apply pagination
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


    def post(self, request, format=None):
        """
        Create a new product with optional image and categories.
        
        Request Body:
        - name: Product name
        - description: Product description
        - mrp: Maximum retail price
        - sellingPice: Selling price
        - ItemQuantityType: Unit type (kg, g, piece, etc.)
        - image: Optional image file or base64 encoded image
        - image_alt: Optional alt text for the image
        - category_ids: Optional list of category IDs
        - is_featured: Whether the product is featured
        - is_active: Whether the product is active
        """
        serializer = ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetail(APIView):
    """
    Retrieve, update or delete a product instance.
    """
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Get a specific product by ID.
        """
        product = self.get_object(pk)
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        """
        Update a product with optional image and categories update.
        
        Request Body:
        - name: Product name
        - description: Product description
        - mrp: Maximum retail price
        - sellingPice: Selling price
        - ItemQuantityType: Unit type (kg, g, piece, etc.)
        - image: Optional image file or base64 encoded image
        - image_alt: Optional alt text for the image
        - category_ids: Optional list of category IDs to update
        - is_featured: Whether the product is featured
        - is_active: Whether the product is active
        """
        product = self.get_object(pk)
        serializer = ProductDetailSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        """
        Delete a product and its associated image.
        """
        product = self.get_object(pk)
        product.delete()  # This will also delete the image file
        return Response(status=status.HTTP_204_NO_CONTENT)

class FeaturedProducts(APIView):
    """
    Get featured products.
    """
    def get(self, request, format=None):
        """
        Get all featured products.
        """
        products = Product.objects.filter(is_featured=True, is_active=True)
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductsByCategory(APIView):
    """
    Get products by category.
    """
    def get(self, request, slug, format=None):
        """
        Get products by category slug.
        """
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return Response(
                {"error": "Category not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        products = Product.objects.filter(categories=category, is_active=True)
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    



class UserCartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """List all cart items for the authenticated user."""
        cart_items = UserCart.objects.filter(user=request.user)
        serializer = UserCartSerializer(cart_items, many=True)
        return Response(serializer.data)



    def post(self, request):
        """Add or update an item in the cart."""
        serializer = UserCartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            cart_item = serializer.save()
            return Response(UserCartSerializer(cart_item).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        """Delete a single item (if pk) or clear the cart (if no pk)."""
        if pk:
            cart_item = get_object_or_404(UserCart, pk=pk, user=request.user)
            cart_item.delete()
            return Response({'message': 'Cart item deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        else:
            cart_items = UserCart.objects.filter(user=request.user)
            deleted_count = cart_items.count()
            cart_items.delete()
            return Response({'message': f'{deleted_count} cart item(s) deleted.'}, status=status.HTTP_204_NO_CONTENT)


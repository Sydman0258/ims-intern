from rest_framework import viewsets
from rest_framework.response import Response

from product.models import Product

from .serializers import ProductDetailSerializer, ProductListSerializer




class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A Simple Viewsets for Product List and Details
    """


    queryset=(Product.objects.all().select_related("retail_unit","retail_unit__mall","retail_unit__tenant").order_by("name")
        )

    def get_serializer_class(self):
       if self.action=="retrieve":
           return ProductDetailSerializer
       return ProductListSerializer
           

# class ProductList(viewsets.ViewSet):
#     serializer_class = ProductListSerializer
#     queryset=Product.objects.all().order_by("name")
#     # def get_queryset(self):
#     #     products = (
#     #         Product.objects
#     #         .select_related(
#     #             "retail_unit",
#     #             "retail_unit__mall",
#     #             "retail_unit__tenant",
#     #         )
#     #         .order_by("name")
#     #     )

#     #     retail_unit_id = self.request.query_params.get("retail_unit")
#     #     if retail_unit_id:
#     #         products = products.filter(retail_unit_id=retail_unit_id)

#     #     return products

#     # def list(self, request, *args, **kwargs):
#     #     queryset = self.filter_queryset(self.get_queryset())
#     #     serializer = self.get_serializer(queryset, many=True)
#     #     return Response({"products": serializer.data})


# class ProductDetail(generics.RetrieveAPIView):
#     serializer_class = ProductDetailSerializer
#     queryset=Product.objects.select_related("retail_unit","retail_unit__mall","retail_unit__tenant")
#   
from rest_framework.pagination import LimitOffsetPagination

class ProductPaginationView(LimitOffsetPagination):
 default_limit=2
 max_limit=10

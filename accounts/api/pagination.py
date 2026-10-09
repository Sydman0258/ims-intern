from rest_framework.pagination import LimitOffsetPagination

class UserPaginationView(LimitOffsetPagination):
 default_limit=2
 max_limit=10

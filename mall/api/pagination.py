from rest_framework.pagination import PageNumberPagination,CursorPagination
# class MallPaginationView(PageNumberPagination):
#     page_size = 5
#     page_size_query_param = 'page_size'
#     max_page_size = 100


class MallPaginationView(CursorPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'

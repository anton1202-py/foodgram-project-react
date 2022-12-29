from rest_framework.pagination import PageNumberPagination


class PagePagination(PageNumberPagination):
    """Пагинатор"""
    page_paginator = 'limit'
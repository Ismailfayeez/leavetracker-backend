from django_filters.rest_framework import FilterSet, filters
from .models import LeaveApproval, LeaveRequest
from django.db.models import Q
import operator
from functools import reduce


class MultiValueCharFilter(filters.BaseCSVFilter, filters.CharFilter):
    def filter(self, qs, value):
        values = value or []
        expr = None
        if len(values) > 0:
            expr = reduce(
                operator.or_,
                (Q(**{f'{self.field_name}__{self.lookup_expr}': v})
                 for v in values)
            )
            print(expr)
        if expr is not None:
            return qs.filter(expr)
        else:
            return qs

from typing import Dict, Optional, List
from django.db.models import QuerySet, Model
from django.core.exceptions import FieldDoesNotExist
import logging

logger = logging.getLogger(__name__)

class QuerysetSorter:
    """
    Queryset sorting utility for Django ORM models.
    Usage:



    sorter = QuerysetSorter(
        queryset=Order.objects.all(),
        order_by="date_created_desc",
        allowed_fields={"date_created": "date_created"},
        default="-date_created"
    )

    sorted_queryset = sorter.sort()

    """

    def __init__(
        self,
        queryset: QuerySet[Model],
        order_by: Optional[str],
        allowed_fields: Dict[str, str],
        default: str
    ) -> None:
        self.queryset = queryset
        self.order_by = order_by.lower() if order_by else None  # ✅ case normalization
        self.allowed_fields = allowed_fields
        self.default = default
        self.model = queryset.model

    def is_valid_field(self, field_name: str) -> bool:
        """
        Validate model field, including related fields (e.g., 'category__name')
        """
        try:
            base_field = field_name.split("__")[0]  # ✅ handle related fields
            self.model._meta.get_field(base_field)
            return True
        except FieldDoesNotExist:
            return False

    def get_default_ordering(self) -> List[str]:
        """
        Ensure default ordering is always valid
        """

        # Support multiple defaults as well
        defaults = self.default.split(",")
        valid_defaults = []

        for field in defaults:
            field = field.strip()
            raw_field = field.lstrip("-")

            if self.is_valid_field(raw_field):
                valid_defaults.append(field)

        return valid_defaults if valid_defaults else [self.default]

    def parse_sorting(self) -> List[str]:
        """
        Parse and validate sorting parameters (supports multi-field sorting)
        """
        if not self.order_by:
            return []

        fields = self.order_by.split(",")
        ordering = []

        for item in fields:
            item = item.strip()

            try:
                field, direction = item.rsplit("_", 1)
            except ValueError:
                logger.warning(f"Invalid sort format: {item}")
                continue

            if direction not in ("asc", "desc"):
                logger.warning(f"Invalid sort direction: {item}")
                continue

            if field not in self.allowed_fields:
                logger.warning(f"Field not allowed for sorting: {field}")
                continue

            model_field = self.allowed_fields[field]

            if not self.is_valid_field(model_field):
                logger.warning(f"Invalid model field: {model_field}")
                continue

            prefix = "-" if direction == "desc" else ""
            ordering.append(f"{prefix}{model_field}")

        return ordering

    def sort(self) -> QuerySet[Model]:
        ordering = self.parse_sorting()

        if not ordering:
            return self.queryset.order_by(*self.get_default_ordering())

        return self.queryset.order_by(*ordering)
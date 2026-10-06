from typing import TypeVar, Generic, Iterable
from django.db import models
from django.db.models import QuerySet, Q
from django.core.exceptions import FieldDoesNotExist

TModel = TypeVar("TModel", bound=models.Model)


class SearchModel(Generic[TModel]):
    """
    Generic search utility for Django ORM models.

    Attributes:
        model (type[TModel]): The Django ORM model to search.
        query_string (str): The search query string.
        fields_to_look (Iterable[str]): List of model field names to search within.
        lookup (str): The type of lookup to perform (default is 'icontains').
    Examples:
        search_util = SearchModel(
            ModelName,
            "search term",
            fields_to_look=["field1", "field2"],
        )
        results = search_util.search()
    """  
    def __init__(
        self,
        model: type[TModel],
        query_string: str,
        fields_to_look: Iterable[str],
        lookup: str = "icontains",
    ):
        if not issubclass(model, models.Model):
            raise TypeError("model must be a Django ORM model")

        self.model = model
        self.query_string = query_string
        self.fields_to_look = list(fields_to_look)
        self.lookup = lookup

        self._validate_fields()

    def _validate_fields(self) -> None:
        for field_path in self.fields_to_look:
            self._validate_field_path(field_path)
        
    def _validate_field_path(self, field_path: str) -> None:
        model = self.model
        parts = field_path.split("__")

        for part in parts:
            try:
                field = model._meta.get_field(part)
            except FieldDoesNotExist:
                raise FieldDoesNotExist(
                    f"The field path '{field_path}' is invalid for model "
                    f"{self.model.__name__}"
                )
            if hasattr(field, 'related_model') and field.related_model:
                model = field.related_model

    def search(self) -> QuerySet[TModel]:
        if not self.query_string:
            return self.model.objects.all()

        q_object = Q()

        for field in self.fields_to_look:
            q_object |= Q(
                **{f"{field}__{self.lookup}": self.query_string}
            )

        return self.model.objects.filter(q_object).distinct()
    


from django.db import models
from django.db.models.fields.related import OneToOneRel, ManyToManyRel, ManyToOneRel

from elasticsearch_dsl.mapping import Mapping
from elasticsearch_dsl.field import Field

from djes.conf import settings

# TODO: expand this for all django field types
FIELD_MAPPINGS = {
    "AutoField": {"type": "long"},
    "OneToOneField": {"type": "long"},
    "ForeignKey": {"type": "long"},
    "ManyToManyField": {"type": "long"},
    "IntegerField": {"type": "long"},
    "CharField": {"type": "string"},
    "TextField": {"type": "string"},
    "SlugField": {"type": "string", "index": "not_analyzed"},
    "DateTimeField": {"type": "date"},
    "DateField": {"type": "date"},
    "BooleanField": {"type": "boolean"}
}


class EmptyMeta(object):
    pass


import pytest

class DjangoMapping(Mapping):
    """A subclass of the elasticsearch_dsl Mapping, allowing the automatic mapping
    of many fields on the model, while letting the developer override these settings"""

    def __init__(self, model):
        # Avoiding circular import
        # from .models import Indexable

        self.model = model
        if not hasattr(self, "Meta"):
            self.Meta = EmptyMeta

        default_name = "{}_{}".format(self.model._meta.app_label, self.model._meta.model_name)
        name = getattr(self.Meta, "doc_type", default_name)

        super(DjangoMapping, self).__init__(name)
        self._meta = {}

        excludes = excludes = getattr(self.Meta, "excludes", [])

        for field in self.model._meta.get_fields():

            if field.auto_created and field.is_relation:
                continue

            db_column, attname = field.db_column, field.attname

            manual_field_mapping = getattr(self, attname, None)
            if manual_field_mapping:
                self.field(db_column or attname, manual_field_mapping)
                continue

            # Checking to make sure this field hasn't been excluded
            if attname in excludes:
                continue

            if field.get_internal_type() == "ManyToManyField" and hasattr(field.rel.to, "from_es"):

                related_properties = field.rel.to.get_mapping().properties.properties.to_dict()
                self.field(field.name, {"type": "nested", "properties": related_properties})
                continue

            if isinstance(field, models.ForeignKey):
                # This is a related field, so it should maybe be nested?

                # We only want to nest fields when they are indexable, and not parent pointers.
                if hasattr(field.rel.to, "from_es") and not field.rel.parent_link:

                    related_properties = field.rel.to.get_mapping().properties.properties.to_dict()
                    self.field(field.name, {"type": "nested", "properties": related_properties})
                    continue

            field_args = FIELD_MAPPINGS.get(field.get_internal_type())
            if field_args:
                self.field(db_column or attname, field_args)
            else:
                raise Warning("Can't find {}".format(field.get_internal_type()))

        # Now any custom fields
        for field in dir(self.__class__):
            manual_field_mapping = getattr(self, field)
            if field not in self.properties.properties.to_dict() and isinstance(manual_field_mapping, Field):
                self.field(field, manual_field_mapping)

        self.properties._params["_id"] = {"path": self.model._meta.pk.name}
        if getattr(self.Meta, "dynamic", "strict") == "strict":
            self.properties._params["dynamic"] = "strict"

    @property
    def index(self):
        return getattr(self.Meta, "index", settings.ES_INDEX)

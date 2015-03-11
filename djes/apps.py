from django.apps import AppConfig

from .models import Indexable
from .mapping import DjangoMapping
from .conf import settings

from elasticsearch_dsl.connections import connections


def get_base_class(cls):
    """finds the absolute base

    :param cls: the class instance
    :type cls: object

    :return: the base class
    :rtype: type
    """
    while cls.__bases__ and cls.__bases__[0] != Indexable:
        cls = cls.__bases__[0]
    return cls


class IndexableRegistry(object):
    """Contains information about all PolymorphicIndexables in the project."""
    def __init__(self):
        self.all_models = {}
        self.families = {}

    def register(self, klass):
        """Adds a new PolymorphicIndexable to the registry."""

        # Get the mapping class for this model
        if hasattr(klass, "Mapping"):
            mapping_klass = type("Mapping", (DjangoMapping, klass.Mapping), {})
        else:
            mapping_klass = DjangoMapping

        # Cache the mapping instance on the model
        klass.mapping = mapping_klass(klass)

        # Now we can get the doc_type
        doc_type = klass.mapping.doc_type

        self.all_models[doc_type] = klass
        base_class = get_base_class(klass)
        if base_class not in self.families:
            self.families[base_class] = {}
        self.families[base_class][doc_type] = klass


    def get_doctypes(self, klass):
        """Returns all the mapping types for a given class."""
        base = get_base_class(klass)
        return self.families[base]

indexable_registry = IndexableRegistry()


class DJESConfig(AppConfig):
    name = 'djes'
    verbose_name = "DJ E.S."

    def ready(self):

        def register_subclasses(klass):
            for subclass in klass.__subclasses__():
                # only register concrete models
                meta = getattr(subclass, "_meta")
                if meta and not getattr(meta, "abstract"):
                    indexable_registry.register(subclass)
                register_subclasses(subclass)
        register_subclasses(Indexable)

    connections.configure(**settings.ES_CONNECTIONS)

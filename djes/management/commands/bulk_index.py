from django.core.management.base import BaseCommand, CommandError
from elasticsearch import TransportError
from elasticsearch_dsl.connections import connections
from elasticsearch.helpers import streaming_bulk

from djes.apps import indexable_registry


def model_iterator(model):
    for obj in model.objects.iterator():
        yield obj.to_dict()


def bulk_index(es, index=None, version=1):

    vindex = "{0}_{1:0>4}".format(index, version)

    es.indices.put_settings(
        index=vindex,
        body={"index": {"refresh_interval": "-1"}}
    )

    for model in indexable_registry.indexes[index]:
        doc_type = model.mapping.doc_type
        for ok, result in streaming_bulk(es, model_iterator(model), index=vindex, doc_type=doc_type):
            continue

    es.indices.put_settings(
        index=vindex,
        body={"index": {"refresh_interval": "1"}}
    )


class Command(BaseCommand):
    help = "Creates ES indices, and ensures that mappings are up to date"

    def handle(self, *args, **options):

        es = connections.get_connection("default")
        bulk_index(es)

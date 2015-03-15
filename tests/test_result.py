from django.core import management
import pytest
from model_mommy import mommy
import time

from example.app.models import SimpleObject, RelatableObject


@pytest.mark.django_db
def test_simple_get(es_client):

    management.call_command("sync_es")

    test_object = mommy.make(SimpleObject)
    time.sleep(1)  # Let the index refresh

    from_es = SimpleObject.search_objects.get(id=test_object.id)
    assert from_es.foo == test_object.foo
    assert from_es.bar == test_object.bar
    assert from_es.baz == test_object.baz
    assert from_es.__class__.__name__ == "SimpleObject_ElasticSearchResult"
    assert from_es.save is None

    with pytest.raises(RelatableObject.DoesNotExist):
        RelatableObject.search_objects.get(id=test_object.id)


@pytest.mark.django_db
def test_related_get(es_client):

    management.call_command("sync_es")

    test_object = mommy.make(RelatableObject)
    time.sleep(1)  # Let the index refresh

    from_es = RelatableObject.search_objects.get(id=test_object.id)
    assert from_es.foo == test_object.foo
    assert from_es.bar == test_object.bar
    assert from_es.baz == test_object.baz
    assert from_es.__class__.__name__ == "SimpleObject_ElasticSearchResult"
    assert from_es.save is None



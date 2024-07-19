import random
import string
import pytest

#pylint:disable=redefined-outer-name,use-dict-literal,missing-timeout,unspecified-encoding,consider-using-with

from utils import TEST_DOJOS_LOCATION
from utils import login, make_dojo_official, create_dojo, create_dojo_yml

@pytest.fixture(scope="session")
def admin_session():
    session = login("admin", "admin")
    yield session


@pytest.fixture
def random_user():
    random_id = "".join(random.choices(string.ascii_lowercase, k=16))
    session = login(random_id, random_id, register=True)
    yield random_id, session


@pytest.fixture(scope="session")
def completionist_user():
    random_id = "".join(random.choices(string.ascii_lowercase, k=16))
    session = login(random_id, random_id, register=True)
    yield random_id, session


@pytest.fixture(scope="session")
def guest_dojo_admin():
    random_id = "".join(random.choices(string.ascii_lowercase, k=16))
    session = login(random_id, random_id, register=True)
    yield random_id, session

@pytest.fixture(scope="session")
def example_dojo(admin_session):
    rid = create_dojo("github","pwncollege/example-dojo", session=admin_session)
    make_dojo_official(rid, admin_session)
    return rid

@pytest.fixture(scope="session")
def belt_dojos(admin_session):
    belt_dojo_rids = {
        color: create_dojo_yml(
            open(TEST_DOJOS_LOCATION / f"fake_{color}.yml").read(), session=admin_session
        ) for color in [ "orange", "yellow", "green","purple","blue" ]
    }
    for rid in belt_dojo_rids.values():
        make_dojo_official(rid, admin_session)
    return belt_dojo_rids

@pytest.fixture(scope="session")
def example_import_dojo(admin_session):
    rid = create_dojo("github","pwncollege/example-import-dojo", session=admin_session)
    make_dojo_official(rid, admin_session)
    return rid

@pytest.fixture(scope="session")
def simple_award_dojo(admin_session):
    return create_dojo_yml(open(TEST_DOJOS_LOCATION / "simple_award_dojo.yml").read(), session=admin_session)

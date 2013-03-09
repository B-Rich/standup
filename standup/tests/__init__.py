import unittest
from functools import wraps

from flask import current_app
from standup import test_settings
from standup.apps.status.models import Project, Status
from standup.apps.users.models import User
from standup.database import get_session
from standup.database.classes import Model
from standup.main import create_app


testing_app = create_app(test_settings)
testing_app.config['TESTING'] = True


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.app = testing_app
        self.client = testing_app.test_client()
        for app in testing_app.installed_apps:
            try:
                __import__('%s.models' % app)
            except ImportError:
                pass
        db = get_session(self.app)
        Model.metadata.create_all(db.bind)

    def tearDown(self):
        db = get_session(self.app)
        Model.metadata.drop_all(db.bind)


def with_save(func):
    """Decorate a model maker to add a `save` kwarg.

    If save=True, the model maker will save the object before returning it.

    """
    @wraps(func)
    def saving_func(*args, **kwargs):
        save = kwargs.pop('save', False)
        ret = func(*args, **kwargs)
        if save:
            db = get_session(testing_app)
            db.add(ret)
            db.commit()
        return ret

    return saving_func


@with_save
def project(**kwargs):
    defaults = dict(name='Test Project',
                    slug='test-project')
    defaults.update(kwargs)

    return Project(**defaults)


@with_save
def user(**kwargs):
    defaults = dict(username='jdoe',
                    name='John Doe',
                    email='john@doe.com',
                    slug='jdoe')
    defaults.update(kwargs)

    return User(**defaults)


@with_save
def status(**kwargs):
    defaults = dict(content='This is a status update.')
    defaults.update(kwargs)

    if 'user' not in kwargs and 'user_id' not in kwargs:
        defaults['user'] = user(save=True)

    if 'project' not in kwargs and 'project_id' not in kwargs:
        defaults['project'] = project(save=True)

    return Status(**defaults)

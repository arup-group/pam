class Policy:
    def __init__(self):
        pass

    def apply_to(self, household, person=None, activity=None):
        raise NotImplementedError('{} is a base class'.format(type(Policy)))
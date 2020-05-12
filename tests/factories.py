# License info goes here.

"""
Test Factory to make fake objects for testing
"""
import factory
from factory.fuzzy import FuzzyChoice
from service.models import Pat, Gender

class PetFactory(factory.Factory):
    """ Creates fake pets that you don't have to feed """

    class Meta:
        model = Pet

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("first_name")
    category = FuzzyChoice(choices=["dog", "cat", "bird", "fish"])
    available = FuzzyChoice(choices=[True, False])
    gender = FuzzyChoice(choices=[Gender.Male, Gender.Female, Gender.Unknown])

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
        model = Pat

    id = factory.Sequence(lambda n: n)
    fname = factory.Faker("first_name")
    lname = factory.Faker("last_name")
    phone_home = factory.Faker("phone_number")
    email = factory.Faker("email")
    city = factory.Faker("city")
    state = factory.Faker("state")
    #resourceType = FuzzyChoice(choices=["Patient", "Nurse", "Doctor", "Staff"])
    available = FuzzyChoice(choices=[True, False])
    gender = FuzzyChoice(choices=[Gender.Male, Gender.Female, Gender.Unknown])

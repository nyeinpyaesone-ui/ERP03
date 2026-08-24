"""Company factory for generating test company data."""

from datetime import datetime
import factory
from factory.faker import Faker
from factory.alchemy import SQLAlchemyModelFactory


class CompanyFactory(SQLAlchemyModelFactory):
    """Factory for creating test companies."""
    
    class Meta:
        model = None
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"
    
    name = Faker("company")
    code = factory.LazyAttribute(lambda o: o.name[:4].upper().replace(" ", "") + str(factory.Faker("pyint", min_value=100, max_value=999).evaluate(None, None, {})))
    industry = Faker("job")
    is_active = True
    
    created_at = factory.LazyFunction(datetime.utcnow)
    
    @classmethod
    def set_model(cls, model_class):
        """Set the model class dynamically."""
        cls.Meta.model = model_class


class BranchFactory(SQLAlchemyModelFactory):
    """Factory for creating test branches."""
    
    class Meta:
        model = None
        sqlalchemy_session = None
    
    name = Faker("city")
    code = factory.LazyAttribute(lambda o: o.name[:3].upper() + str(factory.Faker("pyint", min_value=10, max_value=99).evaluate(None, None, {})))
    is_active = True
    
    @classmethod
    def set_model(cls, model_class):
        cls.Meta.model = model_class


def create_company_hierarchy(count: int = 5) -> list:
    """Create companies with branches."""
    companies = []
    
    for _ in range(count):
        company = CompanyFactory()
        companies.append(company)
    
    return companies

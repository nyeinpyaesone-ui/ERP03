import os
os.environ['DATABASE_URL'] = 'sqlite:///./test_erp.db'
os.environ['SECRET_KEY'] = 'test-secret-key-for-development-only-12345'
os.environ['TESTING'] = 'true'

from app.main import app
from fastapi.testclient import TestClient
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)

print("=== Testing CRM Business Operations ===")

# Register and login
user_data = {"email": "crm@example.com", "password": "TestPass123!", "full_name": "CRM User"}
client.post('/api/v1/auth/register', json=user_data)
login_data = {"username": "crm@example.com", "password": "TestPass123!"}
response = client.post('/api/v1/auth/login', data=login_data)
token = response.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}

print("\n1. Creating a company...")
company_data = {
    "name": "Acme Corp",
    "industry": "Technology",
    "size": "50-200",
    "website": "https://acme.com"
}
response = client.post('/api/v1/crm/companies', json=company_data, headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    company = response.json()
    print(f"   Company created: {company['name']} (ID: {company['id']})")
    
    print("\n2. Listing companies...")
    response = client.get('/api/v1/crm/companies', headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        companies = response.json()
        print(f"   Companies found: {len(companies)}")
        for c in companies:
            print(f"      - {c['name']} ({c['industry']})")
    
    print("\n3. Creating a contact...")
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@acme.com",
        "phone": "+1234567890",
        "company_id": company['id']
    }
    response = client.post('/api/v1/crm/contacts', json=contact_data, headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        contact = response.json()
        print(f"   Contact created: {contact['first_name']} {contact['last_name']}")
        
        print("\n4. Listing contacts...")
        response = client.get('/api/v1/crm/contacts', headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            contacts = response.json()
            print(f"   Contacts found: {len(contacts)}")

print("\n=== CRM Flow Test Complete ===")

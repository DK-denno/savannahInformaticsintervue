# E-commerce Platform API

## Overview
This project is a RESTful API backend for an e-commerce platform with user management, organization management, product catalog, and order processing functionality. The system uses Firebase for authentication and authorization, PostgreSQL as the primary database, and is deployed via Docker using GitHub Actions.

## Key Features
- User authentication with Firebase
- Role-based access control (RBAC) For Individual Endpoints.
- Organization management
- Product catalog management
- Order processing system
- Communications system setup, email and sms
- Comprehensive test coverage (35 test cases)

## API Documentation

### Authentication
All endpoints (except `/test_view/`) require a valid Firebase authentication token in the `Authorization` header.

### API Endpoints

#### 1. Test Endpoint
- **GET** `/test_view/`
- Description: Basic test endpoint to verify API is running
- Authentication: None
- Returns: Simple success message

#### 2. User Management
- **POST** `/createNewUser/`
  - Creates a new standard user account
  - Required fields: email, password, user details

- **POST** `/adminCreateNewUser/`
  - Admin-only endpoint to create new users
  - Can assign roles and organizations during creation

- **GET** `/getUserDetails/`
  - Retrieves details of the authenticated user
  - Returns: User profile information

#### 3. Organization Management
- **POST** `/createOrganisation/`
  - Creates a new organization
  - Admin-only endpoint

- **GET** `/getOrganisationDetails/`
  - Retrieves details of the authenticated user's organization
  - Organization admins get more detailed information

#### 4. Role Management
- **POST** `/createRoles/`
  - Creates new RBAC roles
  - Admin-only endpoint

- **GET** `/getRoles/`
  - Lists all available roles
  - Returns: Array of role objects

- **POST** `/adminAdRbacTasks/`
  - Assigns RBAC tasks/permissions to roles
  - Admin-only endpoint

#### 5. Product Catalog
- **POST** `/adminAddProductCategories/`
  - Adds new product categories
  - Admin-only endpoint

- **GET** `/adminListProductCategories/`
  - Lists all product categories
  - Returns: Array of category objects

- **POST** `/adminAddProducts/`
  - Adds new products to the catalog
  - Admin-only endpoint

- **GET** `/adminListProducts/`
  - Lists all products in the catalog
  - Returns: Array of product objects

#### 6. Order Processing
- **POST** `/creatOrder/`
  - Creates a new order
  - Customer endpoint

- **GET** `/adminListOrders/`
  - Lists all orders in the system
  - Admin-only endpoint

- **GET** `/clientListOrders/`
  - Lists orders for the authenticated user
  - Customer endpoint

## Technical Stack
- **Backend**: Django REST Framework
- **Authentication**: Firebase
- **Database**: PostgreSQL
- **Testing**: Django Test Framework (35 test cases)
- **CI/CD**: GitHub Actions
- **Deployment**: Docker containers pushed to Docker Hub

## Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL
- Firebase project with authentication enabled
- Docker (for deployment)

### Installation
1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables (see `.env.example`)
5. Run migrations: `python manage.py migrate`
6. Start the development server: `python manage.py runserver`

### Testing
```bash
python manage.py test
```

## Deployment
The project is configured with GitHub Actions to automatically build and push Docker images to Docker Hub on pushes to the main branch.

## Environment Variables
Required environment variables:
```
export pub_key=""
export secret=
export SECRET_KEY=""
export MODE=""
export DEBUG=True
export DB_NAME=
export DB_USER=
export DB_PASSWORD=
export DB_HOST=""
export DB_PORT=
export DATABASE_URL=""
export FIREBASE_CREDENTIALS_PATH=""
export AT_USERNAME=
export AT_API_KEY=
export RESEND_EMAIL_API_KEY=""
export RESEND_TO_MAIL=""
export RESEND_EMAIL_URL=""
export TEST_DB_NAME=
export TEST_DB_USER=
export TEST_DB_PASSWORD=
export TEST_DB_HOST=""
export TEST_DB_PORT=
```

## Future Enhancements
- Add product search and filtering
- Implement payment processing
- Add inventory management
- Expand RBAC system with more granular permissions
- Add API documentation with Swagger/OpenAPI

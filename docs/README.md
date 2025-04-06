# FastAPI Multiple Databases Documentation

Welcome to the documentation for the FastAPI Multiple Databases application. This documentation provides comprehensive guides for setting up, configuring, and using the application.

## Setup Guides

- [Local Setup Guide](local_setup.md) - Instructions for setting up the application in a local environment without Docker
- [Docker Setup Guide](docker_setup.md) - Detailed guide for running the application using Docker
- [Jupyter Integration Guide](jupyter_integration.md) - How to use Jupyter Lab with the application
- [Configuration Guide](../CONFIGURATION.md) - Detailed information about configuration options

## Architecture

The application follows a model-centric architecture with support for multiple database types:

- **PostgreSQL**: Relational database with strong ACID compliance
- **SQL Server**: Microsoft's enterprise relational database
- **MongoDB**: NoSQL document database

Each model in the application can be stored in any of these database types, with automatic schema management and data conversion.

## Key Features

- **Multiple Database Support**: Connect to PostgreSQL, SQL Server, or MongoDB
- **Role-Based Access Control**: Secure endpoints with role and permission-based authentication
- **Automatic API Documentation**: OpenAPI documentation with examples for all endpoints
- **Jupyter Integration**: Built-in Jupyter Lab for data analysis and exploration
- **Flexible Configuration**: Support for both Docker and non-Docker environments

## Getting Started

1. Set up your environment using the setup script:
   ```bash
   python setup_env.py
   ```

2. Choose your preferred deployment method:
   - [Local Setup](local_setup.md)
   - [Docker Setup](docker_setup.md)

3. Access the API documentation at:
   ```
   http://localhost:8000/docs
   ```

## Development Workflow

The project follows a test-driven development process:

1. Write tests for new features
2. Implement the features
3. Ensure tests pass with good coverage
4. Push changes to git when features are complete

## Package Management

The project uses [UV](https://docs.astral.sh/uv/) for package management, with support for traditional pip as well.

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [UV Documentation](https://docs.astral.sh/uv/)

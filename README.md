# FastAPI Scaffolding with Multiple Database Support

A configurable FastAPI server that supports multiple database ecosystems (PostgreSQL, MySQL, SQL Server, MongoDB) with features for authentication, authorization, rate limiting, error logging, and async job processing.

## Features

- **Multiple Database Support**: Connect to PostgreSQL, MySQL, SQL Server, or MongoDB
- **Configuration-Driven**: Easily configure the application through environment variables
- **Authentication & Authorization**: Secure API endpoints with JWT authentication and role-based access control
- **Route Guards**: Protect routes based on user roles and permissions
- **Microservice Communication**: Interact with other microservices
- **Rate Limiting**: Prevent abuse of your API
- **Error Logging**: Comprehensive logging for debugging and monitoring
- **Async Job Processing**: Handle long-running tasks asynchronously

## Project Structure

The project follows a modular structure with clear separation of concerns:

```
app/
├── core/         # Core functionality (config, security, logging)
├── api/          # API routes and dependencies
├── db/           # Database adapters for different database systems
├── models/       # Domain models
├── schemas/      # Pydantic schemas for request/response validation
└── services/     # Business logic and services
```

## Development

This project uses `uv` for dependency management and follows test-driven development practices.

### Setup

1. Clone the repository
2. Install dependencies with `uv sync`
3. Configure environment variables
4. Run the development server

### Testing

Run tests with pytest:

```bash
pytest
```

## Docker

Docker configuration is available in the `docker` directory, which includes Jupyter Lab for interactive development.

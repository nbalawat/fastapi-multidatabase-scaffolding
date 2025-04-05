# MongoDB Troubleshooting Guide

## Common Authentication Errors

### Authentication Failed Error

If you encounter an error like this:

```
pymongo.errors.OperationFailure: Authentication failed., full error: {'ok': 0.0, 'errmsg': 'Authentication failed.', 'code': 18, 'codeName': 'AuthenticationFailed'}
```

This indicates that MongoDB rejected the authentication credentials. Here are the steps to resolve this issue:

## Step 1: Verify Environment Variables

Check that your MongoDB connection string and credentials are correctly set in your environment variables:

```bash
# Example environment variables
MONGODB_URI=mongodb://username:password@mongodb:27017/
MONGODB_DATABASE=fastapi_db
```

## Step 2: Check Docker Compose Configuration

If you're using Docker, verify the MongoDB service configuration in your `docker-compose.yml` file:

```yaml
services:
  mongodb:
    image: mongo:latest
    environment:
      MONGO_INITDB_ROOT_USERNAME: username
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: fastapi_db
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"
```

Ensure that:
- The `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` match the credentials in your connection string
- The MongoDB service is properly networked with your application service

## Step 3: Check MongoDB Connection in Application

Review your database connection code in `app/db/mongodb.py` or similar files:

```python
from pymongo import MongoClient
from app.core.config import settings

def get_mongodb_client():
    """Get MongoDB client."""
    client = MongoClient(settings.MONGODB_URI)
    return client

def get_database():
    """Get MongoDB database."""
    client = get_mongodb_client()
    return client[settings.MONGODB_DATABASE]
```

## Step 4: Verify MongoDB is Running and Accessible

Run these commands to check if MongoDB is running and accessible:

```bash
# Check if MongoDB container is running
docker ps | grep mongodb

# Connect to MongoDB container
docker exec -it <mongodb_container_id> bash

# Connect to MongoDB shell
mongosh -u username -p password --authenticationDatabase admin
```

## Step 5: Check MongoDB Logs

Examine the MongoDB logs for more detailed error information:

```bash
docker logs <mongodb_container_id>
```

## Step 6: Reset MongoDB Authentication

If necessary, you can reset the MongoDB authentication:

1. Stop the MongoDB container
2. Remove the MongoDB volume to clear existing data:
   ```bash
   docker-compose down -v
   ```
3. Update credentials in your docker-compose.yml and environment variables
4. Restart the services:
   ```bash
   docker-compose up -d
   ```

## Step 7: Update MongoDB Adapter Configuration

Ensure your MongoDB adapter is properly configured in `app/db/adapters.py`:

```python
class MongoDBAdapter(BaseAdapter):
    """MongoDB adapter implementation."""
    
    def __init__(self, client, database_name):
        """Initialize MongoDB adapter."""
        self.client = client
        self.db = client[database_name]
        
    async def connect(self):
        """Connect to MongoDB."""
        # MongoDB client is already connected
        return self
```

## Step 8: Check Authentication Mechanism

MongoDB supports different authentication mechanisms. Make sure you're using the correct one:

```python
from pymongo import MongoClient

# For SCRAM-SHA-1 authentication (default)
client = MongoClient(
    "mongodb://username:password@mongodb:27017/",
    authSource="admin",
    authMechanism="SCRAM-SHA-1"
)
```

## Step 9: Verify Database User Permissions

Ensure the MongoDB user has the correct permissions:

```javascript
// Connect to MongoDB as admin
use admin

// Create a user with appropriate permissions
db.createUser({
  user: "username",
  pwd: "password",
  roles: [
    { role: "readWrite", db: "fastapi_db" },
    { role: "dbAdmin", db: "fastapi_db" }
  ]
})
```

## Step 10: Test Connection Independently

Test the MongoDB connection independently of your application:

```python
from pymongo import MongoClient

# Test connection
try:
    client = MongoClient("mongodb://username:password@mongodb:27017/", serverSelectionTimeoutMS=5000)
    print(client.server_info())
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
```

## Other Common MongoDB Issues

### Connection Timeout

If you encounter connection timeouts, check:
- Network connectivity between services
- MongoDB service is running
- Firewall settings

### Database Not Found

If a database or collection is not found:
- Verify the database name in your configuration
- Check if the collection exists
- Ensure the database is initialized properly

### Slow Queries

For slow MongoDB queries:
- Add appropriate indexes
- Review query patterns
- Check MongoDB server resources

## MongoDB Best Practices for This Application

1. **Use Connection Pooling**: MongoDB client already implements connection pooling, but ensure your adapter properly reuses connections

2. **Implement Retry Logic**: Add retry logic for transient MongoDB errors:
   ```python
   from pymongo.errors import ConnectionFailure
   from tenacity import retry, stop_after_attempt, wait_fixed

   @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
   async def safe_db_operation(func, *args, **kwargs):
       try:
           return await func(*args, **kwargs)
       except ConnectionFailure as e:
           logger.error(f"MongoDB connection failure: {e}")
           raise
   ```

3. **Use Proper Indexes**: Create indexes for frequently queried fields:
   ```python
   # In your database initialization code
   db.users.create_index("username", unique=True)
   db.notes.create_index("user_id")
   ```

4. **Handle MongoDB-specific UUID Conversion**: Ensure proper handling of UUIDs with MongoDB:
   ```python
   from bson import Binary
   from uuid import UUID

   # Convert UUID to BSON Binary for MongoDB
   def uuid_to_binary(uuid_obj):
       if isinstance(uuid_obj, UUID):
           return Binary.from_uuid(uuid_obj)
       return uuid_obj
   ```

## Conclusion

Most MongoDB authentication issues can be resolved by verifying credentials, checking connection strings, and ensuring proper configuration. If you continue to experience issues after following these steps, check the MongoDB documentation or consider reaching out to MongoDB support.

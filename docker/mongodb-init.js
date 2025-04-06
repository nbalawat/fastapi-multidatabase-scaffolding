// MongoDB initialization script
// This script creates the database and user for the application

// Switch to admin database to create the user
db = db.getSiblingDB('admin');

// Check if the user already exists
const userExists = db.getUser("${MONGODB_USER}");

if (!userExists) {
    // Create the admin user
    db.createUser({
        user: "${MONGODB_USER}",
        pwd: "${MONGODB_PASSWORD}",
        roles: [
            { role: "userAdminAnyDatabase", db: "admin" },
            { role: "readWriteAnyDatabase", db: "admin" },
            { role: "dbAdminAnyDatabase", db: "admin" }
        ]
    });
    
    print("MongoDB admin user created successfully");
} else {
    print("MongoDB admin user already exists");
}

// Switch to the application database
db = db.getSiblingDB("${MONGODB_DB}");

// Create collections if they don't exist
db.createCollection("users");
db.createCollection("notes");

print("MongoDB initialization completed successfully");

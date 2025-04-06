#!/bin/bash
# MongoDB initialization script with environment variable substitution

# Replace environment variables in the JS file
envsubst < /docker-entrypoint-initdb.d/mongodb-init.js > /tmp/mongodb-init.js

# Execute the script
mongosh admin /tmp/mongodb-init.js

echo "MongoDB initialization completed"

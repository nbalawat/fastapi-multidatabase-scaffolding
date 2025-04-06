// MongoDB initialization script

// Access environment variables passed to the container
const adminDb = db.getSiblingDB('admin');
const appDbName = _getEnv('MONGO_INITDB_DATABASE') || 'fastapi_db';
const username = _getEnv('MONGO_INITDB_ROOT_USERNAME') || 'mongodb';
const password = _getEnv('MONGO_INITDB_ROOT_PASSWORD') || 'mongodb';

print(`Setting up MongoDB with username: ${username}, database: ${appDbName}`);

// Check if the user already exists to avoid errors on container restart
let userExists = false;
try {
  userExists = adminDb.getUser(username) != null;
} catch (e) {
  print(`Error checking if user exists: ${e}`);
}

if (!userExists) {
  try {
    // Create the admin user
    adminDb.createUser({
      user: username,
      pwd: password,
      roles: [
        { role: 'userAdminAnyDatabase', db: 'admin' },
        { role: 'readWriteAnyDatabase', db: 'admin' },
        { role: 'dbAdminAnyDatabase', db: 'admin' }
      ]
    });
    print(`Created admin user: ${username}`);
  } catch (e) {
    print(`Error creating admin user: ${e}`);
  }
}

// Switch to the application database
const appDb = db.getSiblingDB(appDbName);

// Create collections if they don't exist
try {
  appDb.createCollection('users');
  print('Created users collection');
} catch (e) {
  // Collection might already exist, which is fine
  print(`Note: ${e}`);
}

try {
  appDb.createCollection('notes');
  print('Created notes collection');
} catch (e) {
  // Collection might already exist, which is fine
  print(`Note: ${e}`);
}

print('MongoDB initialization completed successfully');

// Helper function to get environment variables
function _getEnv(name) {
  if (typeof process !== 'undefined' && process.env && process.env[name]) {
    return process.env[name];
  } else if (typeof env !== 'undefined' && env[name]) {
    return env[name];
  }
  return null;
}

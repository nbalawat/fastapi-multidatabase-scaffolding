#!/bin/bash
# Script to set up ODBC drivers for SQL Server in Docker

set -e

echo "Setting up ODBC drivers for SQL Server..."

# Install required packages
apt-get update
apt-get install -y --no-install-recommends \
    gnupg2 \
    curl \
    unixodbc \
    unixodbc-dev \
    tdsodbc \
    freetds-bin \
    freetds-dev

# Try to install Microsoft ODBC Driver
echo "Attempting to install Microsoft ODBC Driver 17 for SQL Server..."
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 || echo "Microsoft ODBC Driver installation failed, using FreeTDS instead"

# Configure ODBC drivers
echo "Configuring ODBC drivers..."

# Find the actual path of the Microsoft ODBC driver if it exists
MS_ODBC_DRIVER_PATH=""
if [ -d "/opt/microsoft/msodbcsql17/lib64" ]; then
    MS_ODBC_DRIVER_PATH=$(find /opt/microsoft/msodbcsql17/lib64 -name "libmsodbcsql-*.so*" | head -1)
    echo "Found Microsoft ODBC driver at: $MS_ODBC_DRIVER_PATH"
fi

# Create odbcinst.ini with multiple driver options
cat > /etc/odbcinst.ini << EOF
[ODBC Driver 17 for SQL Server]
Description=Microsoft ODBC Driver 17 for SQL Server
Driver=${MS_ODBC_DRIVER_PATH:-/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.so.1.1}
UsageCount=1

[FreeTDS]
Description=FreeTDS Driver
Driver=/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup=/usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
UsageCount=1

[TDS]
Description=TDS Driver
Driver=/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so
Setup=/usr/lib/x86_64-linux-gnu/odbc/libtdsS.so
UsageCount=1
EOF

# Create a test odbc.ini file
cat > /etc/odbc.ini << EOF
[MSSQL]
Driver=ODBC Driver 17 for SQL Server
Server=sqlserver
Port=1433
Database=master
EOF

echo "ODBC driver setup complete."
ls -la /etc/odbcinst.ini
cat /etc/odbcinst.ini

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "Setup completed successfully."

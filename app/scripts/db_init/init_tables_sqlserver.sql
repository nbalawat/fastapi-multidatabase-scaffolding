-- Initialize database tables for FastAPI Multiple Databases application (SQL Server version)

-- We're already connected to the correct database from Python
-- so we don't need to create it or use it here

-- Drop existing tables if they exist to ensure clean schema
IF OBJECT_ID(N'[dbo].[items]', N'U') IS NOT NULL
    DROP TABLE [dbo].[items];
GO

IF OBJECT_ID(N'[dbo].[notes]', N'U') IS NOT NULL
    DROP TABLE [dbo].[notes];
GO

IF OBJECT_ID(N'[dbo].[users]', N'U') IS NOT NULL
    DROP TABLE [dbo].[users];
GO

IF OBJECT_ID(N'[dbo].[roles]', N'U') IS NOT NULL
    DROP TABLE [dbo].[roles];
GO

-- Users table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[users] (
        [id] NVARCHAR(255) PRIMARY KEY,
        [email] NVARCHAR(255) NOT NULL,
        [username] NVARCHAR(255) NOT NULL,
        [hashed_password] NVARCHAR(255) NOT NULL,
        [full_name] NVARCHAR(255) NULL,
        [disabled] BIT DEFAULT 0,
        [role] NVARCHAR(50) NOT NULL
    );

    -- Create unique constraints
    ALTER TABLE [dbo].[users] ADD CONSTRAINT UQ_users_email UNIQUE ([email]);
    ALTER TABLE [dbo].[users] ADD CONSTRAINT UQ_users_username UNIQUE ([username]);

    -- Create indexes
    CREATE INDEX idx_users_email ON [dbo].[users]([email]);
    CREATE INDEX idx_users_username ON [dbo].[users]([username]);
END
GO

-- Notes table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[notes]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[notes] (
        [id] NVARCHAR(255) PRIMARY KEY,
        [title] NVARCHAR(255) NOT NULL,
        [content] NVARCHAR(MAX) NULL,
        [visibility] NVARCHAR(50) DEFAULT 'private',
        [tags] NVARCHAR(MAX) NULL,
        [user_id] NVARCHAR(255) NOT NULL,
        [created_at] DATETIME2 DEFAULT GETUTCDATE(),
        [updated_at] DATETIME2 NULL
    );

    -- Create index on user_id
    CREATE INDEX idx_notes_user_id ON [dbo].[notes]([user_id]);
END
GO

-- Items table (example)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[items]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[items] (
        [id] NVARCHAR(255) PRIMARY KEY,
        [title] NVARCHAR(255) NOT NULL,
        [description] NVARCHAR(MAX) NULL,
        [owner_id] NVARCHAR(255) NULL,
        [created_at] DATETIME2 DEFAULT GETUTCDATE()
    );

    -- Create foreign key constraint
    ALTER TABLE [dbo].[items] ADD CONSTRAINT FK_items_users 
    FOREIGN KEY ([owner_id]) REFERENCES [dbo].[users]([id]);

    -- Create index on owner_id
    CREATE INDEX idx_items_owner_id ON [dbo].[items]([owner_id]);
END
GO

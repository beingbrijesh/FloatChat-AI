-- Drop tables in the correct order to respect dependencies
DROP TABLE IF EXISTS tech CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS meta CASCADE;
DROP TABLE IF EXISTS processedfiles CASCADE;

----------------------------------------------------------------------
-- Table for meta.nc files. This is the PARENT table.
-- It only starts with the primary key. All other columns are added by the script.
----------------------------------------------------------------------
CREATE TABLE meta (
    platform_number VARCHAR(32) PRIMARY KEY,
    -- The python script will automatically add columns like 'project_name', 'pi_name', etc.
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

----------------------------------------------------------------------
-- Table for prof.nc files. This is a CHILD table linked to 'meta'.
----------------------------------------------------------------------
CREATE TABLE profiles (
    platform_number VARCHAR(32) NOT NULL,
    cycle_number INTEGER NOT NULL,
    -- The python script will add 'direction', 'juld', 'latitude', etc.
    PRIMARY KEY (platform_number, cycle_number),
    CONSTRAINT fk_meta
        FOREIGN KEY(platform_number)
        REFERENCES meta(platform_number)
        ON DELETE CASCADE
);

----------------------------------------------------------------------
-- Table for tech.nc files. Also a CHILD table linked to 'meta'.
----------------------------------------------------------------------
CREATE TABLE tech (
    platform_number VARCHAR(32) NOT NULL,
    cycle_number INTEGER NOT NULL, -- Assuming tech files are also per-cycle
    -- The python script will add all technical parameter columns.
    PRIMARY KEY (platform_number, cycle_number),
    CONSTRAINT fk_meta
        FOREIGN KEY(platform_number)
        REFERENCES meta(platform_number)
        ON DELETE CASCADE
);

----------------------------------------------------------------------
-- Utility table for tracking processed files (remains the same)
----------------------------------------------------------------------
CREATE TABLE processedfiles (
    filename TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

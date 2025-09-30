-- Creates an index on the primary lookup columns for the profiles table
CREATE INDEX idx_profiles_platform_cycle ON profiles (platform_number, cycle_number);

-- Creates an index on the filename for quick checks in the processedfiles table
CREATE INDEX idx_processedfiles_filename ON processedfiles (filename);
-- ================================================
-- Master Query: View all tables, counts, and data
-- (GUI-friendly version with row numbers)
-- ================================================

-- 🔧 Toggle preview mode here:
--   set to 50   → show only first 50 rows
--   set to NULL → show all rows
WITH settings AS (
    SELECT 50::INT AS limit_rows   -- change here
)

-- 1. List all tables
SELECT '--- Available Tables ---' AS section, NULL AS info;
SELECT table_name AS table, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 2. Row counts for sanity check
SELECT '--- Row Counts ---' AS section, NULL AS info;
SELECT 'profiles' AS table, COUNT(*) AS rows FROM profiles
UNION ALL
SELECT 'measurements', COUNT(*) FROM measurements
UNION ALL
SELECT 'parameters', COUNT(*) FROM parameters
UNION ALL
SELECT 'history', COUNT(*) FROM history
UNION ALL
SELECT 'calibration', COUNT(*) FROM calibration
UNION ALL
SELECT 'processedfiles', COUNT(*) FROM processedfiles;

-- 3. Dump contents of each table with ordering and row numbers

-- Profiles
SELECT '--- Profiles ---' AS section, NULL AS info;
SELECT row_number() OVER (ORDER BY platform_number, cycle_number) AS row_num,
       p.*
FROM profiles p, settings s
ORDER BY platform_number, cycle_number
LIMIT COALESCE(s.limit_rows, ALL);

-- Measurements
SELECT '--- Measurements ---' AS section, NULL AS info;
SELECT row_number() OVER (ORDER BY platform_number, cycle_number, level_index, parameter) AS row_num,
       m.*
FROM measurements m, settings s
ORDER BY platform_number, cycle_number, level_index, parameter
LIMIT COALESCE(s.limit_rows, ALL);

-- Parameters
SELECT '--- Parameters ---' AS section, NULL AS info;
SELECT row_number() OVER (ORDER BY platform_number, cycle_number, parameter) AS row_num,
       pr.*
FROM parameters pr, settings s
ORDER BY platform_number, cycle_number, parameter
LIMIT COALESCE(s.limit_rows, ALL);

-- History
SELECT '--- History ---' AS section, NULL AS info;
SELECT row_number() OVER (ORDER BY platform_number, cycle_number, history_index, parameter) AS row_num,
       h.*
FROM history h, settings s
ORDER BY platform_number, cycle_number, history_index, parameter
LIMIT COALESCE(s.limit_rows, ALL);

-- Calibration
SELECT '--- Calibration ---' AS section, NULL AS info;
SELECT row_number() OVER (ORDER BY platform_number, cycle_number, parameter) AS row_num,
       c.*
FROM calibration c, settings s
ORDER BY platform_number, cycle_number, parameter
LIMIT COALESCE(s.limit_rows, ALL);

-- Processed Files
SELECT '--- Processed Files ---' AS section, NULL AS info;
SELECT row_number() OVER (ORDER BY processed_at DESC) AS row_num,
       f.*
FROM processedfiles f, settings s
ORDER BY processed_at DESC
LIMIT COALESCE(s.limit_rows, ALL);

-- Recreate the working TPM_Config table structure
IF OBJECT_ID('dbo.TPM_Config', 'U') IS NOT NULL
    DROP TABLE dbo.TPM_Config;

CREATE TABLE dbo.TPM_Config (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value NVARCHAR(1000)
);

-- Optional: seed default values
INSERT INTO dbo.TPM_Config (setting_key, setting_value) VALUES
('API_URL', ''),
('API_TOKEN', ''),
('API_ID', ''),
('LOG_LEVEL', 'DEBUG'),
('BASE_DIR', '');
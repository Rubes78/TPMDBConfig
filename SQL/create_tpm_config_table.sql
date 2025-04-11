-- Create the TPM_Config table
CREATE TABLE TPM_Config (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value NVARCHAR(1000)
);

-- Insert values from the INI
INSERT INTO TPM_Config (setting_key, setting_value) VALUES
('api_userName', 'GWSactoUser'),
('api_password', 'PpTHvkXADncZW2x5'),
('api_companyID', '815311'),
('api_url', 'http://tpmapi-prd.rcsaero.com/RcsItems'),
('db_name', 'TPMDataRCS3'),
('db_server', 'holosql'),
('db_user', 'sa'),
('db_password', 'CounterPoint8'),
('db_logLevel', 'INFO'),
('batch_size', '5000'),
('batch_delay', '0.2');

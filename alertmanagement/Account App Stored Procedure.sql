DELIMITER //

CREATE PROCEDURE sp_register_citizen(
    IN p_first_name VARCHAR(50),
    IN p_middle_name VARCHAR(50),
    IN p_last_name VARCHAR(50),
    IN p_email VARCHAR(254),
    IN p_phone_number VARCHAR(15),
    IN p_password_hash VARCHAR(128), -- We expect the HASHED password for security
    OUT p_status VARCHAR(50),
    OUT p_message VARCHAR(255)
)
BEGIN
    -- Variables to hold the auto-generated IDs
    DECLARE v_auth_id INT;
    DECLARE v_custom_user_id INT;
    
    -- Error Handler to Rollback if any insert fails (Ensures Atomicity)
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = 'ERROR';
        SET p_message = 'Database transaction failed. Registration aborted.';
    END;

    -- ---------------------------------------------------------
    -- 1. VALIDATION CHECKS (Satisfies "Validates Inputs" & "Prevents Duplicates")
    -- ---------------------------------------------------------
    
    -- Check 1: Duplicate Email
    IF EXISTS (SELECT 1 FROM auth_user WHERE email = p_email) THEN
        SET p_status = 'FAILED';
        SET p_message = 'Email address is already registered.';
        
    -- Check 2: Phone Number Length (Satisfies "11 characters length" requirement)
    ELSEIF LENGTH(p_phone_number) != 11 THEN
        SET p_status = 'FAILED';
        SET p_message = 'Phone number must be exactly 11 characters.';
        
    ELSE
        -- -----------------------------------------------------
        -- 2. DATA INSERTION (Atomic Transaction)
        -- -----------------------------------------------------
        START TRANSACTION;

        -- A. Insert into Django's auth_user (The Login Credentials)
        INSERT INTO auth_user (
            username, 
            password, 
            email, 
            first_name, 
            last_name, 
            is_superuser, 
            is_staff, 
            is_active, 
            date_joined
        ) VALUES (
            p_email,           -- We use email as the username
            p_password_hash,   -- SECURE: Stores the hash, not plain text
            p_email, 
            p_first_name, 
            p_last_name, 
            0, 0, 1, NOW()     -- Standard Django defaults
        );
        
        -- Capture the ID of the user we just created
        SET v_auth_id = LAST_INSERT_ID();

        -- B. Insert into your Custom User model (account_user)
        INSERT INTO account_user (
            account_id,        -- The OneToOne Link to auth_user
            role, 
            first_name, 
            middle_name, 
            last_name, 
            email_address, 
            phone_number, 
            created_at, 
            updated_at
        ) VALUES (
            v_auth_id, 
            'citizen',         -- Default role
            p_first_name, 
            p_middle_name, 
            p_last_name, 
            p_email, 
            p_phone_number, 
            NOW(), 
            NOW()
        );

        -- Capture the ID of the custom profile we just created
        SET v_custom_user_id = LAST_INSERT_ID();

        -- C. Insert into the Citizen Table (account_citizen)
        INSERT INTO account_citizen (user_id_id)
        VALUES (v_custom_user_id);

        -- If we got here, everything worked. Commit the changes.
        COMMIT;

        SET p_status = 'SUCCESS';
        SET p_message = 'Account created successfully.';
        
    END IF;

END //

DELIMITER ;
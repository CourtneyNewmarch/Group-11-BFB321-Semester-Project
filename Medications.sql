-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS stock_updates;
DROP TABLE IF EXISTS batches;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS pharmacy_personnel;

--create suppliers table
CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL, 
    contact_person TEXT,
    phone TEXT,
    email TEXT,
    address TEXT
);

--create medications table
CREATE TABLE medications (
    medication_id TEXT PRIMARY KEY,
    medication_name TEXT NOT NULL UNIQUE,
    medication_category TEXT,
    safety_stock_level INTEGER,
    unit_price REAL NOT NULL,
    supplier_id INTEGER NOT NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

--create batches table
CREATE TABLE batches (
batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
quantity INTEGER,
expiry_date DATE, 
medication_id TEXT NOT NULL,
FOREIGN KEY (medication_id) REFERENCES medications(medication_id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
);

-- Create pharmacy personnel_table
CREATE TABLE pharmacy_personnel (
    username TEXT PRIMARY KEY,
    full_name_and_surname TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

--create stock_updates table
CREATE TABLE stock_updates (
    update_id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id TEXT NOT NULL,
    supplier_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    username TEXT,
    update_type TEXT NOT NULL CHECK (update_type IN ('add', 'remove', 'set')),
    quantity_change INTEGER NOT NULL,
    old_quantity INTEGER NOT NULL,
    new_quantity INTEGER NOT NULL,
    reason TEXT NOT NULL CHECK (reason IN ('restock', 'sale', 'damage', 'return', 'adjustment', 'other')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    FOREIGN KEY (medication_id) REFERENCES medications(medication_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    FOREIGN KEY (username) REFERENCES pharmacy_personnel(username)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- Create customers table
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    full_name_and_surname TEXT NOT NULL,
    password TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('external_user', 'internal_user')),
    order_id INTEGER, 
    item_ordered TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

--insert sample pharmacy_personnel
INSERT INTO pharmacy_personnel (username, full_name_and_surname, password) VALUES
('ZPerry', 'Tyla Perry', 'Yt88*x4'),
('GMaxulu', 'Gomolemo Maxulu', 'gdR77$wP');

--insert sample suppliers
INSERT INTO suppliers (supplier_name, contact_person, phone, email, address) VALUES
('MedNet', 'Rorisang', '+27-556-123', 'rman@yahoo.com', '77 Bond Ave'),
('BigPharma', 'Perry', '+27-443-212', 'court@gmail.com', '21 Loveville');

--insert sample medications
INSERT INTO medications (medication_id, medication_name, medication_category, safety_stock_level, unit_price, supplier_id) VALUES
('M-324', 'efavirenz', 'ARV', 55, 50.99, 1),
('N-442', 'rifampin', 'TB', 30, 45.99, 2);

--insert sample batches 
INSERT INTO batches (quantity, expiry_date, medication_id) VALUES
(100, '2025-10-27', 'M-324'),
(80, '2025-10-29', 'N-442');

--insert sample stock_updates
INSERT INTO stock_updates (medication_id, supplier_id, batch_id, username, update_type, quantity_change, old_quantity, new_quantity, reason) VALUES
('M-324', 1, 1, 'ZPerry', 'add', 7, 2, 9, 'restock'),
('N-442', 2, 2, 'GMaxulu', 'remove', 10, 22, 12, 'sale');

--insert sample customers
INSERT INTO customers (customer_id, full_name_and_surname, password, user_type, order_id, item_ordered) VALUES
('FN8772', 'Court Kadash', 'Rv22xb#', 'internal_user', 5, 'rifampin'),
('9006150085081', 'Tino Mukiwa', 'piLtt68', 'external_user', 7, 'efavirenz');








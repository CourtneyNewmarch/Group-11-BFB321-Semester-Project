# Group-11-BFB321-Semester-Project
## erDiagram
    product_categories {
        INTEGER category_id PK
        TEXT category_name UK
        TEXT category_description
        DATETIME created_at
    }
    
    vendors {
        INTEGER vendor_id PK
        TEXT first_name
        TEXT last_name
        TEXT business_name
        TEXT email UK
        TEXT phone
        TEXT address
        TEXT password
        DATETIME created_at
        DATETIME updated_at
    }
    
    products {
        INTEGER product_id PK
        TEXT sku UK
        TEXT product_name
        INTEGER category_id FK
        INTEGER quantity
        REAL price
        TEXT description
        TEXT supplier
        INTEGER min_stock_level
        INTEGER max_stock_level
        DATETIME created_at
        DATETIME updated_at
    }
    
    stock_updates {
        INTEGER update_id PK
        INTEGER product_id FK
        INTEGER vendor_id FK
        TEXT update_type
        INTEGER quantity_change
        INTEGER old_quantity
        INTEGER new_quantity
        TEXT reason
        TEXT notes
        DATETIME created_at
    }

    product_categories ||--o{ products : "categorizes"
    vendors ||--o{ stock_updates : "performs"
    products ||--o{ stock_updates : "tracks"
erDiagram
    product_categories {
        INTEGER category_id PK
        TEXT category_name UK
        TEXT category_description
        DATETIME created_at
    }
    
    vendors {
        INTEGER vendor_id PK
        TEXT first_name
        TEXT last_name
        TEXT business_name
        TEXT email UK
        TEXT phone
        TEXT address
        TEXT password
        DATETIME created_at
        DATETIME updated_at
    }
    
    products {
        INTEGER product_id PK
        TEXT sku UK
        TEXT product_name
        INTEGER category_id FK
        INTEGER quantity
        REAL price
        TEXT description
        TEXT supplier
        INTEGER min_stock_level
        INTEGER max_stock_level
        DATETIME created_at
        DATETIME updated_at
    }
    
    stock_updates {
        INTEGER update_id PK
        INTEGER product_id FK
        INTEGER vendor_id FK
        TEXT update_type
        INTEGER quantity_change
        INTEGER old_quantity
        INTEGER new_quantity
        TEXT reason
        TEXT notes
        DATETIME created_at
    }

    product_categories ||--o{ products : "categorizes"
    vendors ||--o{ stock_updates : "performs"
    products ||--o{ stock_updates : "tracks"

# Group-11-BFB321-Semester-Project
## Group Members

| Name | Student Number |
|--------------------|---------------|
| Rorisang Dithato   | u22594168     |
| Zhaneley Perry     | u23606488     |
| Courtney Newmarch  | u23531089     |
| Tinotenda Mukiwa   | u22750861     |

# Medical Inventory Management System
A web-based pharmaceutical inventory management systems that functions to reduce medicine stockouts in South African healthcare facilities. The system is built with HTML, Bootstrap, CSS and SQLite.

# Features
- Dashboard: A summary view of medication inventory statistics and user activity  
- Order Tracking: A detailed overview of the quantities and delivery dates of orders in the system  
- Product Management: Add, view and remove medications in the system  
- Stock Tracking: Update stock levels with detailed statistics  
- Customer Management: Control customer use and track order histories for predictive analytics  
- Supplier Management: Monitor supplier performance and streamline procurement

# Database Setup
1. Open command prompt/terminal in the project directory
2. Run the SQL commands:  
        sqlite3 Medications.db < Medications.sql

# Database Schema
## Entity Relationship Diagram (ERD)
```mermaid  
erDiagram
    suppliers {
        INTEGER supplier_id PK
        TEXT supplier_name
        TEXT contact_person
        TEXT phone
        TEXT email
        TEXT address
    }
    
    medications {
        TEXT medication_id PK
        TEXT medication_name UK
        TEXT medication_category
        INTEGER safety_stock_level
        REAL unit_price
        INTEGER supplier_id FK
    }
    
    batches {
        INTEGER batch_id PK
        INTEGER quantity
        DATE expiry_date
        TEXT medication_id FK
    }
    
    stock_updates {
        INTEGER update_id PK
        TEXT medication_id FK
        INTEGER supplier_id FK
        INTEGER batch_id FK
        TEXT update_type
        INTEGER quantity_change
        INTEGER old_quantity
        INTEGER new_quantity
        TEXT reason
        DATETIME created_at
    }
    
    customers {
        TEXT customer_id PK
        TEXT full_name_and_surname
        TEXT password
        TEXT user_type
        INTEGER order_id
        TEXT item_ordered
        DATETIME created_at
    }
    
    pharmacy_personnel {
        TEXT username PK
        TEXT full_name_and_surname
        TEXT password
        DATETIME created_at
    }

    suppliers ||--o{ medications : "supplies"
    medications ||--o{ batches : "contains"
    medications ||--o{ stock_updates : "tracks"
    suppliers ||--o{ stock_updates : "records"
    batches ||--o{ stock_updates : "references"
    customers }o--o{ medications : "orders"
    pharmacy_personnel }o--o{ stock_updates : "manages"

    %% Color Styling
    classDef suppliers fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000
    classDef medications fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000
    classDef batches fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px,color:#000
    classDef stock_updates fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef customers fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#000
    classDef pharmacy_personnel fill:#fce4ec,stroke:#ad1457,stroke-width:2px,color:#000
    
    class suppliers suppliers
    class medications medications
    class batches batches
    class stock_updates stock_updates
    class customers customers
    class pharmacy_personnel pharmacy_personnel
```
This Database includes the following tables:    
## Tables
1. __Suppliers__: Medication suppliers
2. **Customers**: Registered customers and their relevant information
3. **Medications**: Contains a variety of medications and their related informartion (category and price)
4. **Batches**: Provides a batch view for ease in medications control (expiry date and quantity)
5. **Pharmacy Personnel**: Details the pharmacy personnel and their user details
6. **Stock Updates**: Tracks medication flow in and out of the system

## Views 
1. __Weekly Deliveries__: view the pending deliveries, completed orders and delayed shipment alerts

# Sample Data
The database includes 2 sample data entries for testing in each table:  
- **2 Pharmacy Personnel**: ZPerry and GMaxulu with their user details
- **2 Suppliers**: Rorisang (MedNet) and Perry (BigPharma), these entries detail the supplier and the industry contact
- **2 Medications**: Efavirenz (category ARV) and Rifampin (category TB)
- **2 Batches**: Details the batch id along with its quantity (100 and 80)
- **2 Stock Updates**: These sample entries detail the update type (add, remove or set) with a reason for the quantity change (eg. "sale")
- **2 Customers**: Court Kadash and Tino Mukiwa along with their respective identity numbers

# File Structure


# Usage
1. Initialize the database using the SQLite command line method above
2. Open LogiTrack.html in your web browser
3. Navigate through the different pages to manage your medication inventory, user data and order creation. The use cases are valid for pharmacy personnel, medication staff and customers.

# Technologies Used
- HTML5: Structure and forms
- Bootstrap 5.3.8: UI framework and styling
- Bootstrap Icons: Icon set
- CSS
- SQLite: Database for data persistence

# Browser Compatibility
The application works with all modern browsers that support HTML5 and CSS3, including:

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+  

Note: This is a static HTML application. For production use, you would need to add backend functionality for database connectivity and form processing.

   
   






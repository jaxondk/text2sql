-- Create sample tables for testing

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    inventory INTEGER DEFAULT 0
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2) NOT NULL
);

-- Order items table
CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Insert sample data
INSERT INTO users (username, email) VALUES 
('john_doe', 'john@example.com'),
('jane_smith', 'jane@example.com'),
('bob_johnson', 'bob@example.com');

INSERT INTO products (name, description, price, inventory) VALUES 
('Laptop', 'High-performance laptop with 16GB RAM', 1299.99, 25),
('Smartphone', '5G smartphone with dual camera', 799.99, 50),
('Headphones', 'Wireless noise-cancelling headphones', 199.99, 100),
('Tablet', '10-inch tablet with retina display', 499.99, 30);

INSERT INTO orders (user_id, total_amount) VALUES 
(1, 1299.99),
(2, 999.98),
(3, 699.97);

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES 
(1, 1, 1, 1299.99),
(2, 2, 1, 799.99),
(2, 3, 1, 199.99),
(3, 4, 1, 499.99),
(3, 3, 1, 199.99); 
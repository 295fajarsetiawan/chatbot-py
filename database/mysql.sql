-- =====================================
-- TABEL USERS
-- =====================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- TABEL PRODUCTS
-- Relasi ke users
-- =====================================
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    nama_product VARCHAR(150) NOT NULL,
    harga DECIMAL(10,2) NOT NULL,
    stok INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_products_user
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);

-- =====================================
-- DATA USERS
-- =====================================
INSERT INTO users (nama, email, password) VALUES
('Fajar Setiawan', 'fajar@gmail.com', '123456'),
('Budi Santoso', 'budi@gmail.com', '123456'),
('Siti Aminah', 'siti@gmail.com', '123456');

-- =====================================
-- DATA PRODUCTS
-- user_id relasi ke users.id
-- =====================================
INSERT INTO products (user_id, nama_product, harga, stok) VALUES
(1, 'Laptop Asus', 8500000, 10),
(1, 'Mouse Logitech', 250000, 25),
(2, 'Keyboard Mechanical', 750000, 15),
(2, 'Monitor LG 24 Inch', 2200000, 8),
(3, 'Headset Gaming', 450000, 20);
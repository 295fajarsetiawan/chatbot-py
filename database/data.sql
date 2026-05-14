-- =====================================
-- INSERT DATA USERS (20 DATA)
-- =====================================
INSERT INTO users (nama, email, password) VALUES
('Andi Wijaya', 'andi@gmail.com', '123456'),
('Rina Marlina', 'rina@gmail.com', '123456'),
('Dewi Lestari', 'dewi@gmail.com', '123456'),
('Agus Saputra', 'agus@gmail.com', '123456'),
('Joko Prasetyo', 'joko@gmail.com', '123456'),
('Lina Kartika', 'lina@gmail.com', '123456'),
('Rahmat Hidayat', 'rahmat@gmail.com', '123456'),
('Yuni Astuti', 'yuni@gmail.com', '123456'),
('Dian Permata', 'dian@gmail.com', '123456'),
('Rudi Hartono', 'rudi@gmail.com', '123456'),
('Tono Sapri', 'tono@gmail.com', '123456'),
('Nina Sari', 'nina@gmail.com', '123456'),
('Arif Nugroho', 'arif@gmail.com', '123456'),
('Putri Ayu', 'putri@gmail.com', '123456'),
('Hendra Gunawan', 'hendra@gmail.com', '123456'),
('Maya Fitri', 'maya@gmail.com', '123456'),
('Ilham Ramadhan', 'ilham@gmail.com', '123456');

-- =====================================
-- INSERT DATA PRODUCTS (50 DATA)
-- =====================================
INSERT INTO products (user_id, nama_product, harga, stok) VALUES
(1, 'Laptop Asus ROG', 15000000, 5),
(1, 'Mouse Logitech G102', 250000, 20),
(1, 'Keyboard Rexus', 450000, 15),

(2, 'Monitor Samsung 24"', 2200000, 10),
(2, 'SSD Samsung 1TB', 1800000, 12),
(2, 'Flashdisk Sandisk 64GB', 120000, 50),

(3, 'Headset Gaming Fantech', 350000, 25),
(3, 'Webcam Logitech C270', 400000, 10),
(3, 'Mousepad RGB', 150000, 30),

(4, 'Printer Epson L3210', 2500000, 8),
(4, 'Tinta Printer Epson', 85000, 40),

(5, 'Kursi Gaming', 1750000, 7),
(5, 'Meja Komputer', 950000, 10),

(6, 'Router TP-Link', 450000, 18),
(6, 'Kabel LAN 10M', 75000, 100),

(7, 'Smartphone Samsung A54', 5200000, 9),
(7, 'Case HP Samsung', 85000, 25),
(7, 'Tempered Glass', 35000, 60),

(8, 'iPhone 13', 12500000, 4),
(8, 'Charger iPhone', 350000, 20),

(9, 'Powerbank Xiaomi 20000mAh', 275000, 15),
(9, 'Kabel USB Type-C', 45000, 80),

(10, 'Speaker Bluetooth JBL', 650000, 13),
(10, 'Microphone Gaming', 550000, 9),

(11, 'TV LG 43 Inch', 4800000, 6),
(11, 'Remote TV Universal', 65000, 30),

(12, 'Laptop Acer Nitro 5', 13500000, 5),
(12, 'Cooling Pad Laptop', 120000, 22),

(13, 'Drone DJI Mini', 7500000, 3),
(13, 'Baterai Drone', 850000, 10),

(14, 'Kamera Canon EOS', 9500000, 4),
(14, 'Tripod Kamera', 250000, 16),

(15, 'Jam Smartwatch Xiaomi', 550000, 14),
(15, 'Strap Smartwatch', 50000, 35),

(16, 'Playstation 5', 9500000, 2),
(16, 'Stick PS5', 1200000, 11),
(16, 'Game FIFA 25', 850000, 17),

(17, 'Nintendo Switch', 5200000, 6),
(17, 'Game Zelda', 950000, 10),

(18, 'Harddisk External 2TB', 1250000, 12),
(18, 'USB Hub 4 Port', 95000, 25),

(19, 'Tablet iPad Air', 9800000, 5),
(19, 'Apple Pencil', 1750000, 7),

(20, 'Smart TV Xiaomi', 4200000, 6),
(20, 'Bracket TV', 150000, 18),

(5, 'Lampu LED RGB', 95000, 40),
(6, 'Keyboard Mechanical RGB', 850000, 14),
(7, 'Mouse Wireless', 175000, 28),
(8, 'Laptop Stand Aluminium', 225000, 19),
(9, 'Headphone Sony', 1450000, 9),
(10, 'Action Camera', 3200000, 5),
(11, 'Ring Light', 275000, 13),
(12, 'Gaming Desk', 2100000, 4),
(13, 'PC Rakitan Gaming', 18500000, 2),
(14, 'RAM DDR4 16GB', 950000, 21),
(15, 'VGA RTX 4070', 12500000, 3);

-- =====================================
-- MENAMPILKAN DATA RELASI USER & PRODUCT
-- =====================================
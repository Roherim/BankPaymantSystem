
CREATE DATABASE payments;

\c payments


CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

INSERT INTO users (username, email) VALUES ('testuser', 'testuser@example.com') ON CONFLICT (username) DO NOTHING;


CREATE TABLE IF NOT EXISTS order_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO order_statuses (name) VALUES ('unpaid'), ('partially_paid'), ('paid') ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS payment_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO payment_statuses (name) VALUES ('pending'), ('completed'), ('cancelled'), ('refunded') ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS payment_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

INSERT INTO payment_types (name) VALUES ('cash'), ('acquiring') ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    status_id INTEGER NOT NULL REFERENCES order_statuses(id) DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO orders (customer_id, amount) VALUES (1, 1000), (1, 10000), (1, 532);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    payment_type_id INTEGER NOT NULL REFERENCES payment_types(id),
    amount INTEGER NOT NULL CHECK (amount > 0),
    status_id INTEGER NOT NULL REFERENCES payment_statuses(id) DEFAULT 1,
    external_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);


CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_status_id ON payments(status_id);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status_id ON orders(status_id);


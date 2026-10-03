-- Таблица складов

CREATE TABLE IF NOT EXISTS warehouses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL
);



-- Таблица товаров

CREATE TABLE IF NOT EXISTS products (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE -- Например: 'Большая игрушка', 'Маленькая игрушка'
);



CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    username TEXT,
    role TEXT NOT NULL, --admin or manager

    warehouse_id BIGINT,

    -- Связываем пользователя со складом:

    FOREIGN KEY (warehouse_id)q
        REFERENCES warehouses(id)
);



CREATE TABLE IF NOT EXISTS inventory (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    quantity BIGINT NOT NULL,
    warehouse_id BIGINT,
    product_id BIGINT,

    FOREIGN KEY (warehouse_id)
    REFERENCES warehouses(id),

    FOREIGN KEY (product_id)
        REFERENCES products(id),
    UNIQUE (warehouse_id, product_id)
);



CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL,
    warehouse_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    operation_type TEXT NOT NULL,

    from_warehouse_id BIGINT, -- Откуда (NULL, если это приход)
    to_warehouse_id BIGINT, -- Куда (NULL, если это расход)

    quantity BIGINT NOT NULL,
    comment TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Внешние ключи:
    FOREIGN KEY (user_id)
        REFERENCES users(id),
    FOREIGN KEY (warehouse_id)
        REFERENCES warehouses(id),
    FOREIGN KEY (product_id)
        REFERENCES products(id),
    FOREIGN KEY (from_warehouse_id)
        REFERENCES warehouses(id),
    FOREIGN KEY (to_warehouse_id)
        REFERENCES warehouses(id)
);
-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tg_id BIGINT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-------------------------------------------------------

-- Таблица заказов (покупка товара: натал, карма, соляр)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    tg_id INTEGER NOT NULL REFERENCES users(tg_id) ON DELETE CASCADE,
    type VARCHAR(32) NOT NULL,               -- 'natal', 'karma', 'solar'
    status VARCHAR(32) NOT NULL DEFAULT 'pending',  -- pending / paid / processing / done / failed
    result TEXT,                              -- итоговый текст от ChatGPT
    ui_message_id BIGINT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-------------------------------------------------------

-- Таблица данных, введённых пользователем (данные заказа)
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    birth_date VARCHAR(32) NOT NULL,          -- дата рождения
    birth_time VARCHAR(32) NOT NULL,          -- время рождения
    birth_city TEXT NOT NULL,                 -- город рождения
    extra_data JSONB DEFAULT '{}'::jsonb,     -- доп. данные (например для соляра — город проживания)
    created_at TIMESTAMP DEFAULT NOW()
);

-------------------------------------------------------

-- Таблица платежей YooKassa
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    yookassa_id VARCHAR(255) NOT NULL,        -- ID платежа на стороне YooKassa
    amount INTEGER NOT NULL,                  -- цена в рублях
    status VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending / waiting_for_capture / succeeded / canceled
    url TEXT NOT NULL,                        -- ссылка на оплату
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-------------------------------------------------------

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-------------------------------------------------------

-- Триггер для автоматического обновления updated_at в orders
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'orders_update_timestamp'
    ) THEN
        CREATE TRIGGER orders_update_timestamp
        BEFORE UPDATE ON orders
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;

-------------------------------------------------------

-- Триггер для автоматического обновления updated_at в payments
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgname = 'payments_update_timestamp'
    ) THEN
        CREATE TRIGGER payments_update_timestamp
        BEFORE UPDATE ON payments
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;

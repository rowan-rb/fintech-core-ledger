-- 1. Renombrar la tabla actual
ALTER TABLE journal_entries RENAME TO journal_entries_old;

-- 2. Crear la tabla particionada por mes
CREATE TABLE journal_entries (
    id UUID NOT NULL,
    transaction_id UUID NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(id),
    amount NUMERIC(19,4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- 3. Partición por defecto (por si hay fechas fuera de rango)
CREATE TABLE journal_entries_default PARTITION OF journal_entries DEFAULT;

-- 4. Migrar los datos existentes
INSERT INTO journal_entries SELECT * FROM journal_entries_old;

-- 5. Borrar la tabla vieja
DROP TABLE journal_entries_old;

-- 6. Recrear el trigger de inmutabilidad en la tabla particionada
CREATE OR REPLACE FUNCTION prevent_ledger_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'COMPLIANCE VIOLATION: Cannot UPDATE or DELETE from the ledger. Ledgers are append-only.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_ledger_update
BEFORE UPDATE OR DELETE ON journal_entries
FOR EACH ROW EXECUTE FUNCTION prevent_ledger_modification();
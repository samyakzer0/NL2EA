BEGIN;

-- ============================================================
-- ZER0LABS STRUCTURED DATABASE
-- EAQL / NL2EA
-- ============================================================

DROP SCHEMA IF EXISTS zer0labs CASCADE;
CREATE SCHEMA zer0labs;


-- ============================================================
-- 1. PLANS
-- ============================================================

CREATE TABLE zer0labs.plans (
    plan_id SERIAL PRIMARY KEY,
    plan_name VARCHAR(50) UNIQUE NOT NULL,
    monthly_price NUMERIC(10,2),
    description TEXT
);

INSERT INTO zer0labs.plans
(plan_name, monthly_price, description)
VALUES
('Developer', 49.00,
 'Entry-level plan for individual developers.'),
('Team', 299.00,
 'Plan for engineering and analytics teams.'),
('Business', 999.00,
 'Plan for growing organizations.'),
('Enterprise', NULL,
 'Custom enterprise pricing.');


-- ============================================================
-- 2. CUSTOMERS
-- ============================================================

CREATE TABLE zer0labs.customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    country VARCHAR(50) NOT NULL,
    industry VARCHAR(100),
    customer_segment VARCHAR(30) NOT NULL,
    acquisition_channel VARCHAR(50),
    signup_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'active',

    CHECK (
        customer_segment IN
        ('Developer', 'Team', 'Business', 'Enterprise')
    ),

    CHECK (
        status IN
        ('active', 'churned', 'trial')
    )
);


-- ============================================================
-- 3. ENTERPRISE CUSTOMERS
-- ============================================================

INSERT INTO zer0labs.customers
(customer_name, country, industry, customer_segment,
 acquisition_channel, signup_date, status)
VALUES
('Northstar Retail Systems',
 'India',
 'Retail Technology',
 'Enterprise',
 'enterprise sales',
 '2026-07-01',
 'active'),

('ApexFin Analytics',
 'India',
 'Financial Technology',
 'Enterprise',
 'enterprise sales',
 '2026-07-08',
 'active'),

('CloudHarbor Systems',
 'USA',
 'Cloud Infrastructure',
 'Enterprise',
 'enterprise sales',
 '2026-07-15',
 'active'),

('Meridian HealthTech',
 'USA',
 'Healthcare Technology',
 'Enterprise',
 'enterprise sales',
 '2026-08-01',
 'active'),

('BluePeak Logistics',
 'Singapore',
 'Logistics',
 'Enterprise',
 'partnerships',
 '2026-08-05',
 'active'),

('Vertex Commerce',
 'India',
 'E-commerce',
 'Enterprise',
 'enterprise sales',
 '2026-08-12',
 'active'),

('AtlasWorks',
 'UK',
 'Business Software',
 'Enterprise',
 'enterprise sales',
 '2026-08-20',
 'active'),

('NovaGrid Energy',
 'India',
 'Energy Technology',
 'Enterprise',
 'partnerships',
 '2026-09-01',
 'active');


-- ============================================================
-- 4. BUSINESS CUSTOMERS
-- 21
-- ============================================================

INSERT INTO zer0labs.customers
(customer_name, country, industry, customer_segment,
 acquisition_channel, signup_date, status)

SELECT
    'Business Customer ' || n,

    CASE n % 4
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'USA'
        WHEN 2 THEN 'UK'
        ELSE 'Singapore'
    END,

    CASE n % 5
        WHEN 0 THEN 'Software'
        WHEN 1 THEN 'E-commerce'
        WHEN 2 THEN 'FinTech'
        WHEN 3 THEN 'Logistics'
        ELSE 'Analytics'
    END,

    'Business',

    CASE n % 4
        WHEN 0 THEN 'referrals'
        WHEN 1 THEN 'Product-led'
        WHEN 2 THEN 'partnerships'
        ELSE 'other'
    END,

    DATE '2026-01-01' + (n * 5),

    'active'

FROM generate_series(1,21) AS n;


-- ============================================================
-- 5. TEAM CUSTOMERS
-- 42
-- ============================================================

INSERT INTO zer0labs.customers
(customer_name, country, industry, customer_segment,
 acquisition_channel, signup_date, status)

SELECT
    'Team Customer ' || n,

    CASE n % 4
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'USA'
        WHEN 2 THEN 'UK'
        ELSE 'Singapore'
    END,

    CASE n % 5
        WHEN 0 THEN 'Software'
        WHEN 1 THEN 'E-commerce'
        WHEN 2 THEN 'FinTech'
        WHEN 3 THEN 'Logistics'
        ELSE 'Analytics'
    END,

    'Team',

    CASE n % 4
        WHEN 0 THEN 'referrals'
        WHEN 1 THEN 'Product-led'
        WHEN 2 THEN 'partnerships'
        ELSE 'other'
    END,

    DATE '2025-10-01' + (n * 5),

    'active'

FROM generate_series(1,42) AS n;


-- ============================================================
-- 6. DEVELOPER CUSTOMERS
-- 38
-- ============================================================

INSERT INTO zer0labs.customers
(customer_name, country, industry, customer_segment,
 acquisition_channel, signup_date, status)

SELECT
    'Developer Customer ' || n,

    CASE n % 4
        WHEN 0 THEN 'India'
        WHEN 1 THEN 'USA'
        WHEN 2 THEN 'UK'
        ELSE 'Singapore'
    END,

    'Software',

    'Developer',

    CASE n % 4
        WHEN 0 THEN 'referrals'
        WHEN 1 THEN 'Product-led'
        WHEN 2 THEN 'partnerships'
        ELSE 'other'
    END,

    DATE '2025-08-01' + (n * 4),

    CASE
        WHEN n <= 11 THEN 'active'
        ELSE 'trial'
    END

FROM generate_series(1,38) AS n;


-- ============================================================
-- 7. EMPLOYEES
-- 42 TOTAL
-- ============================================================

CREATE TABLE zer0labs.employees (
    employee_id SERIAL PRIMARY KEY,
    employee_name VARCHAR(120) NOT NULL,
    department VARCHAR(50) NOT NULL,
    role VARCHAR(100),
    hire_date DATE,
    employment_status VARCHAR(30) DEFAULT 'active'
);


-- Engineering: 19

INSERT INTO zer0labs.employees
(employee_name, department, role, hire_date)

SELECT
    'Engineering Employee ' || n,
    'Engineering',

    CASE
        WHEN n <= 3 THEN 'Senior Software Engineer'
        WHEN n <= 10 THEN 'Software Engineer'
        WHEN n <= 15 THEN 'Backend Engineer'
        ELSE 'Data Engineer'
    END,

    DATE '2025-07-15' + (n * 7)

FROM generate_series(1,19) n;


-- Sales: 7

INSERT INTO zer0labs.employees
(employee_name, department, role, hire_date)

SELECT
    'Sales Employee ' || n,
    'Sales',

    CASE
        WHEN n <= 2 THEN 'Enterprise Account Executive'
        ELSE 'Sales Executive'
    END,

    DATE '2025-08-01' + (n * 10)

FROM generate_series(1,7) n;


-- Customer Success: 6

INSERT INTO zer0labs.employees
(employee_name, department, role, hire_date)

SELECT
    'Customer Success Employee ' || n,
    'Customer Success',

    CASE
        WHEN n <= 2 THEN 'Customer Success Manager'
        ELSE 'Customer Success Specialist'
    END,

    DATE '2025-08-01' + (n * 12)

FROM generate_series(1,6) n;


-- Operations: 4

INSERT INTO zer0labs.employees
(employee_name, department, role, hire_date)

SELECT
    'Operations Employee ' || n,
    'Operations',
    'Operations Specialist',
    DATE '2025-08-01' + (n * 14)

FROM generate_series(1,4) n;


-- Finance: 3

INSERT INTO zer0labs.employees
(employee_name, department, role, hire_date)

SELECT
    'Finance Employee ' || n,
    'Finance',

    CASE
        WHEN n = 1 THEN 'Finance Manager'
        ELSE 'Financial Analyst'
    END,

    DATE '2025-08-01' + (n * 16)

FROM generate_series(1,3) n;


-- Marketing: 3

INSERT INTO zer0labs.employees
(employee_name, department, role, hire_date)

SELECT
    'Marketing Employee ' || n,
    'Marketing',

    CASE
        WHEN n = 1 THEN 'Marketing Manager'
        ELSE 'Growth Specialist'
    END,

    DATE '2025-08-01' + (n * 18)

FROM generate_series(1,3) n;


-- ============================================================
-- 8. SUBSCRIPTIONS
-- ============================================================

CREATE TABLE zer0labs.subscriptions (
    subscription_id SERIAL PRIMARY KEY,

    customer_id INT NOT NULL
        REFERENCES zer0labs.customers(customer_id),

    plan_id INT NOT NULL
        REFERENCES zer0labs.plans(plan_id),

    start_date DATE NOT NULL,

    end_date DATE,

    status VARCHAR(30) NOT NULL,

    monthly_price NUMERIC(10,2),

    CHECK (
        status IN
        ('active', 'cancelled', 'trial')
    )
);


-- ============================================================
-- 9. SUBSCRIPTIONS
-- 82 PAYING CUSTOMERS
-- ============================================================

-- Enterprise = 8

INSERT INTO zer0labs.subscriptions
(customer_id, plan_id, start_date, status, monthly_price)

SELECT
    c.customer_id,
    p.plan_id,
    c.signup_date,
    'active',
    NULL

FROM zer0labs.customers c

JOIN zer0labs.plans p
    ON p.plan_name = 'Enterprise'

WHERE c.customer_segment = 'Enterprise';


-- Business = 21

INSERT INTO zer0labs.subscriptions
(customer_id, plan_id, start_date, status, monthly_price)

SELECT
    c.customer_id,
    p.plan_id,
    c.signup_date,
    'active',
    999.00

FROM zer0labs.customers c

JOIN zer0labs.plans p
    ON p.plan_name = 'Business'

WHERE c.customer_segment = 'Business';


-- Team = 42

INSERT INTO zer0labs.subscriptions
(customer_id, plan_id, start_date, status, monthly_price)

SELECT
    c.customer_id,
    p.plan_id,
    c.signup_date,
    'active',
    299.00

FROM zer0labs.customers c

JOIN zer0labs.plans p
    ON p.plan_name = 'Team'

WHERE c.customer_segment = 'Team';


-- Developer = 11 paying customers

INSERT INTO zer0labs.subscriptions
(customer_id, plan_id, start_date, status, monthly_price)

SELECT
    c.customer_id,
    p.plan_id,
    c.signup_date,
    'active',
    49.00

FROM zer0labs.customers c

JOIN zer0labs.plans p
    ON p.plan_name = 'Developer'

WHERE c.customer_segment = 'Developer'
AND c.customer_name IN (
    SELECT 'Developer Customer ' || n
    FROM generate_series(1,11) n
);


-- ============================================================
-- 10. INVOICES
-- ============================================================

CREATE TABLE zer0labs.invoices (
    invoice_id SERIAL PRIMARY KEY,

    customer_id INT NOT NULL
        REFERENCES zer0labs.customers(customer_id),

    invoice_date DATE NOT NULL,

    due_date DATE NOT NULL,

    amount NUMERIC(12,2) NOT NULL,

    status VARCHAR(30) NOT NULL,

    billing_month DATE NOT NULL,

    CHECK (
        status IN
        ('paid', 'pending', 'overdue', 'void')
    )
);


-- ============================================================
-- 11. ENTERPRISE Q3 INVOICES
-- EXACTLY $111,400
-- ============================================================

INSERT INTO zer0labs.invoices
(
    customer_id,
    invoice_date,
    due_date,
    amount,
    status,
    billing_month
)

SELECT
    c.customer_id,
    DATE '2026-09-30',
    DATE '2026-10-30',
    v.amount,
    'paid',
    DATE '2026-09-01'

FROM (
    VALUES
        ('Northstar Retail Systems', 21000.00),
        ('ApexFin Analytics', 18500.00),
        ('CloudHarbor Systems', 17500.00),
        ('Meridian HealthTech', 15000.00),
        ('BluePeak Logistics', 12500.00),
        ('Vertex Commerce', 11500.00),
        ('AtlasWorks', 9500.00),
        ('NovaGrid Energy', 5900.00)
) AS v(customer_name, amount)

JOIN zer0labs.customers c
    ON c.customer_name = v.customer_name;


-- ============================================================
-- 12. NON-ENTERPRISE Q3 INVOICES
-- ============================================================

INSERT INTO zer0labs.invoices
(
    customer_id,
    invoice_date,
    due_date,
    amount,
    status,
    billing_month
)

SELECT
    s.customer_id,
    m.invoice_date,
    m.invoice_date + 30,
    s.monthly_price,
    'paid',
    DATE_TRUNC(
        'month',
        m.invoice_date
    )::date

FROM zer0labs.subscriptions s

CROSS JOIN (
    VALUES
        (DATE '2026-07-31'),
        (DATE '2026-08-31'),
        (DATE '2026-09-30')
) AS m(invoice_date)

WHERE s.monthly_price IS NOT NULL;


-- ============================================================
-- 13. PAYMENTS
-- ============================================================

CREATE TABLE zer0labs.payments (
    payment_id SERIAL PRIMARY KEY,

    invoice_id INT NOT NULL
        REFERENCES zer0labs.invoices(invoice_id),

    payment_date DATE NOT NULL,

    amount NUMERIC(12,2) NOT NULL,

    payment_method VARCHAR(30),

    status VARCHAR(30) NOT NULL,

    transaction_reference VARCHAR(100)
);


INSERT INTO zer0labs.payments
(
    invoice_id,
    payment_date,
    amount,
    payment_method,
    status,
    transaction_reference
)

SELECT
    invoice_id,
    invoice_date + 5,
    amount,

    CASE invoice_id % 3
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'bank_transfer'
        ELSE 'upi'
    END,

    'completed',

    'Z0PAY-' ||
    LPAD(invoice_id::TEXT, 8, '0')

FROM zer0labs.invoices

WHERE status = 'paid';


-- ============================================================
-- 14. API USAGE
-- ============================================================

CREATE TABLE zer0labs.usage (
    usage_id BIGSERIAL PRIMARY KEY,

    customer_id INT NOT NULL
        REFERENCES zer0labs.customers(customer_id),

    usage_date DATE NOT NULL,

    api_requests BIGINT NOT NULL,

    sql_queries BIGINT NOT NULL,

    rag_queries BIGINT NOT NULL,

    data_processed_gb NUMERIC(12,2),

    CHECK (api_requests >= 0),
    CHECK (sql_queries >= 0),
    CHECK (rag_queries >= 0)
);


-- ============================================================
-- 15. JULY
-- EXACTLY 2.1M REQUESTS
-- ============================================================

INSERT INTO zer0labs.usage
(
    customer_id,
    usage_date,
    api_requests,
    sql_queries,
    rag_queries,
    data_processed_gb
)

SELECT
    s.customer_id,
    DATE '2026-07-31',

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN 2100000 - (81 * 25000)
        ELSE 25000
    END,

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN (2100000 - (81 * 25000)) * 60 / 100
        ELSE 15000
    END,

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN (2100000 - (81 * 25000)) * 20 / 100
        ELSE 5000
    END,

    25.00

FROM zer0labs.subscriptions s;


-- ============================================================
-- 16. AUGUST
-- EXACTLY 2.7M REQUESTS
-- ============================================================

INSERT INTO zer0labs.usage
(
    customer_id,
    usage_date,
    api_requests,
    sql_queries,
    rag_queries,
    data_processed_gb
)

SELECT
    s.customer_id,
    DATE '2026-08-31',

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN 2700000 - (81 * 32000)
        ELSE 32000
    END,

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN (2700000 - (81 * 32000)) * 60 / 100
        ELSE 19200
    END,

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN (2700000 - (81 * 32000)) * 20 / 100
        ELSE 6400
    END,

    32.00

FROM zer0labs.subscriptions s;


-- ============================================================
-- 17. SEPTEMBER
-- EXACTLY 3.6M REQUESTS
-- ============================================================

INSERT INTO zer0labs.usage
(
    customer_id,
    usage_date,
    api_requests,
    sql_queries,
    rag_queries,
    data_processed_gb
)

SELECT
    s.customer_id,
    DATE '2026-09-30',

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN 3600000 - (81 * 43000)
        ELSE 43000
    END,

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN (3600000 - (81 * 43000)) * 60 / 100
        ELSE 25800
    END,

    CASE
        WHEN ROW_NUMBER() OVER (
            ORDER BY s.customer_id
        ) = 1
        THEN (3600000 - (81 * 43000)) * 20 / 100
        ELSE 8600
    END,

    43.00

FROM zer0labs.subscriptions s;


-- ============================================================
-- 18. INDEXES
-- ============================================================

CREATE INDEX idx_customers_country
ON zer0labs.customers(country);

CREATE INDEX idx_customers_segment
ON zer0labs.customers(customer_segment);

CREATE INDEX idx_customers_status
ON zer0labs.customers(status);

CREATE INDEX idx_subscriptions_customer
ON zer0labs.subscriptions(customer_id);

CREATE INDEX idx_subscriptions_plan
ON zer0labs.subscriptions(plan_id);

CREATE INDEX idx_invoices_customer
ON zer0labs.invoices(customer_id);

CREATE INDEX idx_invoices_date
ON zer0labs.invoices(invoice_date);

CREATE INDEX idx_payments_invoice
ON zer0labs.payments(invoice_id);

CREATE INDEX idx_usage_customer
ON zer0labs.usage(customer_id);

CREATE INDEX idx_usage_date
ON zer0labs.usage(usage_date);


-- ============================================================
-- 19. ANALYTICS VIEWS
-- ============================================================

CREATE VIEW zer0labs.customer_revenue_summary AS

SELECT
    c.customer_id,
    c.customer_name,
    c.country,
    c.customer_segment,

    COALESCE(
        SUM(i.amount),
        0
    ) AS total_revenue,

    COUNT(i.invoice_id) AS invoice_count

FROM zer0labs.customers c

LEFT JOIN zer0labs.invoices i
    ON c.customer_id = i.customer_id

GROUP BY
    c.customer_id,
    c.customer_name,
    c.country,
    c.customer_segment;


CREATE VIEW zer0labs.monthly_usage_summary AS

SELECT
    usage_date,
    SUM(api_requests) AS api_requests,
    SUM(sql_queries) AS sql_queries,
    SUM(rag_queries) AS rag_queries,
    SUM(data_processed_gb) AS data_processed_gb

FROM zer0labs.usage

GROUP BY usage_date

ORDER BY usage_date;


-- ============================================================
-- 20. FINAL VALIDATION
-- ============================================================

DO $$
DECLARE
    customers_count INT;
    employees_count INT;
    paying_count INT;
    total_requests BIGINT;
    enterprise_revenue NUMERIC;
BEGIN

    SELECT COUNT(*)
    INTO customers_count
    FROM zer0labs.customers;

    SELECT COUNT(*)
    INTO employees_count
    FROM zer0labs.employees;

    SELECT COUNT(*)
    INTO paying_count
    FROM zer0labs.subscriptions;

    SELECT COALESCE(SUM(api_requests), 0)
    INTO total_requests
    FROM zer0labs.usage;

    SELECT COALESCE(SUM(i.amount), 0)
    INTO enterprise_revenue

    FROM zer0labs.invoices i

    JOIN zer0labs.customers c
        ON i.customer_id = c.customer_id

    WHERE c.customer_segment = 'Enterprise'
      AND i.billing_month = DATE '2026-09-01';


    RAISE NOTICE 'Customers: %', customers_count;
    RAISE NOTICE 'Employees: %', employees_count;
    RAISE NOTICE 'Paying customers: %', paying_count;
    RAISE NOTICE 'Q3 API requests: %', total_requests;
    RAISE NOTICE 'Enterprise Q3 revenue: %', enterprise_revenue;


    IF customers_count <> 109 THEN
        RAISE EXCEPTION
        'Expected 109 customers, got %',
        customers_count;
    END IF;


    IF employees_count <> 42 THEN
        RAISE EXCEPTION
        'Expected 42 employees, got %',
        employees_count;
    END IF;


    IF paying_count <> 82 THEN
        RAISE EXCEPTION
        'Expected 82 paying customers, got %',
        paying_count;
    END IF;


    IF total_requests <> 8400000 THEN
        RAISE EXCEPTION
        'Expected 8400000 API requests, got %',
        total_requests;
    END IF;


    IF enterprise_revenue <> 111400 THEN
        RAISE EXCEPTION
        'Expected 111400 enterprise revenue, got %',
        enterprise_revenue;
    END IF;

END $$;


COMMIT;
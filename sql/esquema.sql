-- ============================================================
-- Esquema de base de datos - Proyecto Integrador
-- Motor: PostgreSQL
-- ============================================================

-- ------------------------------------------------------------
-- Tabla: usuarios
-- Almacena los usuarios autorizados para ingresar al sistema.
-- La contraseña se guarda como HASH (nunca en texto plano).
-- El campo usuario es UNIQUE para evitar duplicados.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id       SERIAL PRIMARY KEY,
    usuario  VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- ------------------------------------------------------------
-- Tabla Estudiantes (Entidad principal)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    telefono VARCHAR(20),
    carrera VARCHAR(100) NOT NULL,
    direccion VARCHAR(200)
);

-- ------------------------------------------------------------
-- Tabla Actividades (Entidad relacionada con FOREIGN KEY)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS actividades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    estudiante_id INT,
    CONSTRAINT fk_estudiante
        FOREIGN KEY (estudiante_id) 
        REFERENCES estudiantes(id) 
        ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- Tabla Recursos
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recursos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    descripcion TEXT,
    cantidad INTEGER NOT NULL
);

-- ------------------------------------------------------------
-- Tabla Rendimiento
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rendimiento (
    id SERIAL PRIMARY KEY,
    estudiante VARCHAR(100) NOT NULL,
    asignatura VARCHAR(100) NOT NULL,
    nota REAL NOT NULL,
    fecha DATE NOT NULL,
    observaciones TEXT
);

-- ============================================================
-- Consultas de verificación
-- ============================================================
SELECT * FROM usuarios;
SELECT * FROM estudiantes;
SELECT * FROM actividades;
SELECT * FROM recursos;
SELECT * FROM rendimiento;


-- ============================================================
-- SEMANA 15: Módulos de Servicios, Productos y Facturación
-- ============================================================

-- ------------------------------------------------------------
-- Tabla: servicios (Categorías de servicios académicos)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS servicios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(50),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- ------------------------------------------------------------
-- Tabla: productos (Items con precio dentro de cada servicio)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    servicio_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio NUMERIC(10, 2) NOT NULL,
    duracion VARCHAR(50),
    modalidad VARCHAR(50),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_servicio_producto
        FOREIGN KEY (servicio_id) 
        REFERENCES servicios(id) 
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Tabla: facturas (Cabecera de facturación)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS facturas (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(10, 2) NOT NULL,
    tipo_pago VARCHAR(20) NOT NULL,
    num_cuotas INT NOT NULL DEFAULT 1,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    fecha_pagada TIMESTAMP,
    CONSTRAINT fk_estudiante_factura
        FOREIGN KEY (estudiante_id) 
        REFERENCES estudiantes(id) 
        ON DELETE RESTRICT,
    CONSTRAINT fk_usuario_factura
        FOREIGN KEY (usuario_id) 
        REFERENCES usuarios(id) 
        ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- Tabla: detalle_factura (Productos dentro de cada factura)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_factura (
    id SERIAL PRIMARY KEY,
    factura_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 1,
    precio_unitario NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(10, 2) NOT NULL,
    CONSTRAINT fk_factura
        FOREIGN KEY (factura_id) 
        REFERENCES facturas(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_producto
        FOREIGN KEY (producto_id) 
        REFERENCES productos(id) 
        ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- Tabla: pagos (Cuotas de cada factura)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pagos (
    id SERIAL PRIMARY KEY,
    factura_id INT NOT NULL,
    numero_cuota INT NOT NULL,
    monto NUMERIC(10, 2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    fecha_pago TIMESTAMP,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    CONSTRAINT fk_factura_pago
        FOREIGN KEY (factura_id) 
        REFERENCES facturas(id) 
        ON DELETE CASCADE
);

-- ============================================================
-- DATOS DE EJEMPLO (Opcional)
-- ============================================================

INSERT INTO servicios (nombre, descripcion, icono) VALUES
('Guías de estudio', 'Material didáctico y guías de apoyo académico', 'book'),
('Planificación de tareas', 'Herramientas para organizar tu tiempo y actividades', 'calendar'),
('Consejos de productividad', 'Recursos para mejorar tu rendimiento académico', 'lightbulb'),
('Herramientas digitales', 'Aplicaciones y licencias para estudiantes', 'laptop')
ON CONFLICT DO NOTHING;

INSERT INTO productos (servicio_id, nombre, descripcion, precio, duracion, modalidad) VALUES
(1, 'Guía de Cálculo Diferencial', 'Guía completa con ejercicios resueltos y práctica.', 15.00, 'PDF digital', 'Online'),
(1, 'Guía de Física Mecánica', 'Resumen teórico y problemas tipo examen.', 12.00, 'PDF digital', 'Online'),
(1, 'Guía de Programación Python', 'Desde variables hasta funciones, con proyectos.', 18.00, 'PDF digital', 'Online'),
(2, 'Asesoría de organización semanal', 'Sesión 1 a 1 para organizar tu semana académica.', 10.00, '1 hora', 'Presencial'),
(2, 'Plantilla de planificación académica', 'Plantilla editable de Excel/Notion.', 5.00, 'Descarga', 'Online'),
(3, 'Curso: Técnicas de estudio efectivas', 'Aprende técnicas como Pomodoro, Feynman y más.', 25.00, '4 semanas', 'Online'),
(4, 'Acceso a Notion Pro (1 mes)', 'Licencia premium de Notion para estudiantes.', 8.00, '1 mes', 'Online'),
(4, 'Licencia Anki (estudiantes)', 'Herramienta de repetición espaciada para memorizar.', 12.00, 'Anual', 'Online');


-- ============================================================
-- SEMANA 15 - ACTUALIZACIÓN: Pagos con método y monto
-- ============================================================

ALTER TABLE pagos ADD COLUMN IF NOT EXISTS monto_pagado NUMERIC(10, 2) DEFAULT 0;

CREATE TABLE IF NOT EXISTS pagos_realizados (
    id SERIAL PRIMARY KEY,
    pago_id INT NOT NULL,
    monto NUMERIC(10, 2) NOT NULL,
    metodo_pago VARCHAR(30) NOT NULL,
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pago_realizado
        FOREIGN KEY (pago_id) REFERENCES pagos(id) ON DELETE CASCADE
);


-- ============================================================
-- Relación Rendimiento ↔ Estudiantes (FK)
-- ============================================================
ALTER TABLE rendimiento ADD COLUMN IF NOT EXISTS estudiante_id INT;

ALTER TABLE rendimiento
DROP CONSTRAINT IF EXISTS fk_estudiante_rendimiento;

ALTER TABLE rendimiento
ADD CONSTRAINT fk_estudiante_rendimiento
FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE;


-- ============================================================
-- Relación Recursos ↔ Servicios (FK)
-- ============================================================
ALTER TABLE recursos ADD COLUMN IF NOT EXISTS servicio_id INT;

ALTER TABLE recursos
DROP CONSTRAINT IF EXISTS fk_servicio_recurso;

ALTER TABLE recursos
ADD CONSTRAINT fk_servicio_recurso
FOREIGN KEY (servicio_id) REFERENCES servicios(id) ON DELETE SET NULL;
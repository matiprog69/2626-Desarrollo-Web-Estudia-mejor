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
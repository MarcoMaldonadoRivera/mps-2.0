-- ================================================================
-- MPS 2.0 — Sistema de Gestión de Impresión
-- Script: mps2_schema.sql
-- Base de datos: MySQL / MariaDB
-- Motor: InnoDB
-- Descripción: Esquema relacional completo para el sistema MPS 2.0
-- ================================================================

-- ================================================================
-- 1. CREACIÓN DE LA BASE DE DATOS
-- ================================================================

CREATE DATABASE IF NOT EXISTS `mps2.0`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `mps2.0`;

-- Desactivar temporalmente las revisiones de claves foráneas
-- para evitar errores durante la creación secuencial de tablas
SET FOREIGN_KEY_CHECKS = 0;


-- ================================================================
-- 2. TABLAS DE IDENTIDAD Y ACCESO
-- ================================================================

-- ---------------------------------------------------------------
-- TABLA: clientes
-- Almacena los datos de cada cliente PYME registrado en el sistema.
-- Cada cliente puede tener múltiples impresoras y usuarios.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `clientes` (
    `ID_cliente`    INT             NOT NULL AUTO_INCREMENT,
    `rut`           VARCHAR(12)     NOT NULL COMMENT 'RUT chileno con formato XX.XXX.XXX-X',
    `razon_social`  VARCHAR(150)    NOT NULL COMMENT 'Nombre legal de la empresa',
    `direccion`     VARCHAR(200)    DEFAULT NULL COMMENT 'Dirección fiscal o comercial',
    `telefono`      VARCHAR(20)     DEFAULT NULL COMMENT 'Teléfono de contacto principal',
    `contacto`      VARCHAR(100)    NOT NULL COMMENT 'Nombre del contacto administrativo',
    `email_contacto` VARCHAR(100)   DEFAULT NULL COMMENT 'Email del contacto',
    `estado`        ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    `fecha_creacion` DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`ID_cliente`),
    UNIQUE KEY `uk_clientes_rut` (`rut`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Clientes PYME registrados en el sistema MPS';


-- ---------------------------------------------------------------
-- TABLA: roles
-- Define los roles de acceso del sistema.
-- Se insertan los 4 roles por defecto según los módulos del frontend.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `roles` (
    `ID_rol`        INT             NOT NULL AUTO_INCREMENT,
    `nombre_rol`    VARCHAR(50)     NOT NULL COMMENT 'Nombre legible del rol',
    `descripcion`   VARCHAR(200)    DEFAULT NULL COMMENT 'Breve descripción de permisos',
    PRIMARY KEY (`ID_rol`),
    UNIQUE KEY `uk_roles_nombre` (`nombre_rol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Roles de acceso del sistema MPS';

-- Insertar roles por defecto (IGNORE evita duplicados al re-ejecutar)
INSERT IGNORE INTO `roles` (`nombre_rol`, `descripcion`) VALUES
    ('Gerente General',   'Acceso total a todos los módulos y reportes ejecutivos'),
    ('Gerente Finanzas',  'Acceso a módulo financiero, costos y reportes de gastos'),
    ('Gerente Técnico',   'Gestión técnica del parque de impresoras y visitas'),
    ('Técnico Freelance', 'Registro de visitas, contadores y suministros asignados');


-- ---------------------------------------------------------------
-- TABLA: usuarios
-- Usuarios del sistema vinculados a un cliente y un rol.
-- Soporta autenticación local (sin OAuth por ahora).
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuarios` (
    `ID_usuario`    INT             NOT NULL AUTO_INCREMENT,
    `ID_cliente`    INT             DEFAULT NULL COMMENT 'NULL si es usuario interno (admin)',
    `ID_rol`        INT             NOT NULL COMMENT 'Rol asignado',
    `nombre`        VARCHAR(100)    NOT NULL COMMENT 'Nombre completo del usuario',
    `email`         VARCHAR(120)    NOT NULL COMMENT 'Email único para login',
    `password`      VARCHAR(255)    NOT NULL COMMENT 'Hash bcrypt de la contraseña',
    `estado`        ENUM('activo', 'inactivo', 'bloqueado') NOT NULL DEFAULT 'activo',
    `ultimo_acceso` DATETIME        DEFAULT NULL,
    `fecha_creacion` DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`ID_usuario`),
    UNIQUE KEY `uk_usuarios_email` (`email`),
    CONSTRAINT `fk_usuarios_cliente`
        FOREIGN KEY (`ID_cliente`) REFERENCES `clientes` (`ID_cliente`)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT `fk_usuarios_rol`
        FOREIGN KEY (`ID_rol`) REFERENCES `roles` (`ID_rol`)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Usuarios del sistema con autenticación y control de acceso';


-- ================================================================
-- 3. TABLAS DEL PARQUE DE IMPRESORAS
-- ================================================================

-- ---------------------------------------------------------------
-- TABLA: departamentos
-- Organiza las impresoras por área/dentro de cada cliente.
-- Permite reportes de costo por departamento.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `departamentos` (
    `ID_departamento`   INT         NOT NULL AUTO_INCREMENT,
    `ID_cliente`        INT         NOT NULL COMMENT 'Cliente propietario',
    `nombre_departamento` VARCHAR(100) NOT NULL COMMENT 'Ej: Administración, Ventas, Bodega',
    PRIMARY KEY (`ID_departamento`),
    CONSTRAINT `fk_departamentos_cliente`
        FOREIGN KEY (`ID_cliente`) REFERENCES `clientes` (`ID_cliente`)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Departamentos/áreas de cada cliente para organizar impresoras';


-- ---------------------------------------------------------------
-- TABLA: impresoras
-- Inventario completo del parque de impresoras.
-- Incluye datos de red (IP, MAC), firmware y garantía.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `impresoras` (
    `ID_impresora`      INT             NOT NULL AUTO_INCREMENT,
    `ID_cliente`        INT             NOT NULL COMMENT 'Cliente propietario',
    `ID_departamento`   INT             DEFAULT NULL COMMENT 'Departamento donde está ubicada',
    `num_serie`         VARCHAR(50)     NOT NULL COMMENT 'Número de serie único del equipo',
    `marca`             VARCHAR(50)     NOT NULL COMMENT 'Ej: HP, Brother, Epson, Samsung',
    `modelo`            VARCHAR(100)    NOT NULL COMMENT 'Modelo completo del equipo',
    `tipo_conexion`     ENUM('USB', 'LAN', 'Wi-Fi', 'USB-LAN') NOT NULL DEFAULT 'LAN',
    `ip`                VARCHAR(15)     DEFAULT NULL COMMENT 'Dirección IPv4 (si aplica)',
    `mac`               VARCHAR(17)     DEFAULT NULL COMMENT 'Dirección MAC (si aplica)',
    `firmware`          VARCHAR(30)     DEFAULT NULL COMMENT 'Versión de firmware actual',
    `fecha_compra`      DATE            DEFAULT NULL,
    `termino_garantia`  DATE            DEFAULT NULL COMMENT 'Fecha fin de garantía del fabricante',
    `ubicacion`         VARCHAR(150)    DEFAULT NULL COMMENT 'Ubicación física / piso',
    `estado_actual`     ENUM('Activo', 'En Reparación', 'De Baja') NOT NULL DEFAULT 'Activo',
    `fecha_creacion`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `fecha_actualizacion` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`ID_impresora`),
    UNIQUE KEY `uk_impresoras_serie` (`num_serie`),
    CONSTRAINT `fk_impresoras_cliente`
        FOREIGN KEY (`ID_cliente`) REFERENCES `clientes` (`ID_cliente`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_impresoras_departamento`
        FOREIGN KEY (`ID_departamento`) REFERENCES `departamentos` (`ID_departamento`)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX `idx_impresoras_estado` (`estado_actual`),
    INDEX `idx_impresoras_garantia` (`termino_garantia`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Inventario del parque de impresoras con datos técnicos y de red';


-- ================================================================
-- 4. TABLAS DE CONSUMIBLES Y OPERACIÓN
-- ================================================================

-- ---------------------------------------------------------------
-- TABLA: suministros
-- Catálogo de consumibles (tóner, drums, fusores, kits).
-- Un mismo suministro puede usarse en múltiples impresoras.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `suministros` (
    `ID_suministro`     INT             NOT NULL AUTO_INCREMENT,
    `tipo`              ENUM('Tóner', 'Drum', 'Fusor', 'Kit Mantención', 'Tinta', 'Otro') NOT NULL,
    `modelo_codigo`     VARCHAR(80)     NOT NULL COMMENT 'Código del modelo del suministro',
    `color`             VARCHAR(20)     DEFAULT NULL COMMENT 'Negro, Cyan, Magenta, Amarillo o NULL si es unitónico',
    `rendimiento_estimado` INT          DEFAULT NULL COMMENT 'Páginas estimadas de vida útil',
    `costo_unitario`    DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT 'Costo en CLP',
    `stock_actual`      INT             NOT NULL DEFAULT 0 COMMENT 'Unidades en bodega',
    `stock_minimo`      INT             NOT NULL DEFAULT 2 COMMENT 'Umbral para alerta de reorden',
    `estado`            ENUM('activo', 'descontinuado') NOT NULL DEFAULT 'activo',
    PRIMARY KEY (`ID_suministro`),
    INDEX `idx_suministros_tipo` (`tipo`),
    INDEX `idx_suministros_stock` (`stock_actual`, `stock_minimo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Catálogo de consumibles y repuestos para impresoras';


-- ---------------------------------------------------------------
-- TABLA: cambio_suministros
-- Registro de cada cambio de consumible realizado en una impresora.
-- Vincula la impresora, el suministro y el técnico que lo hizo.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `cambio_suministros` (
    `ID_cambio`         INT             NOT NULL AUTO_INCREMENT,
    `ID_impresora`      INT             NOT NULL,
    `ID_suministro`     INT             NOT NULL,
    `ID_usuario`        INT             NOT NULL COMMENT 'Técnico que realizó el cambio',
    `fecha_cambio`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `nivel_anterior`    INT             DEFAULT NULL COMMENT 'Nivel porcentaje anterior del suministro',
    `contador_cambio`   INT             DEFAULT NULL COMMENT 'Lectura del contador al momento del cambio',
    `observaciones`     VARCHAR(300)    DEFAULT NULL,
    PRIMARY KEY (`ID_cambio`),
    CONSTRAINT `fk_cambio_impresora`
        FOREIGN KEY (`ID_impresora`) REFERENCES `impresoras` (`ID_impresora`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_cambio_suministro`
        FOREIGN KEY (`ID_suministro`) REFERENCES `suministros` (`ID_suministro`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_cambio_usuario`
        FOREIGN KEY (`ID_usuario`) REFERENCES `usuarios` (`ID_usuario`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX `idx_cambio_fecha` (`fecha_cambio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Historial de cambios de suministros por impresora';


-- ================================================================
-- 5. TABLAS DE MÉTRICAS Y SOPORTE TÉCNICO
-- ================================================================

-- ---------------------------------------------------------------
-- TABLA: historial_contadores
-- Registro mensual de lecturas de contador de cada impresora.
-- Calcula automáticamente las páginas impresas del mes.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `historial_contadores` (
    `ID_contador`       INT             NOT NULL AUTO_INCREMENT,
    `ID_impresora`      INT             NOT NULL,
    `ID_usuario`        INT             NOT NULL COMMENT 'Técnico que registró la lectura',
    `fecha_lectura`     DATE            NOT NULL,
    `contador_inicial`  INT             NOT NULL DEFAULT 0 COMMENT 'Lectura del mes anterior',
    `contador_mensual`  INT             NOT NULL DEFAULT 0 COMMENT 'Lectura actual del equipo',
    `paginas_mes`       INT             NOT NULL DEFAULT 0 COMMENT 'Diferencia calculada',
    PRIMARY KEY (`ID_contador`),
    CONSTRAINT `fk_contadores_impresora`
        FOREIGN KEY (`ID_impresora`) REFERENCES `impresoras` (`ID_impresora`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_contadores_usuario`
        FOREIGN KEY (`ID_usuario`) REFERENCES `usuarios` (`ID_usuario`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX `idx_contadores_fecha` (`fecha_lectura`),
    INDEX `idx_contadores_impresora_fecha` (`ID_impresora`, `fecha_lectura`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Lecturas mensuales de contadores de páginas por impresora';


-- ---------------------------------------------------------------
-- TABLA: visitas_tecnicas
-- Registro de cada visita técnica (preventiva o correctiva).
-- Almacena el reporte completo y el costo asociado.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `visitas_tecnicas` (
    `ID_visita`         INT             NOT NULL AUTO_INCREMENT,
    `ID_impresora`      INT             NOT NULL,
    `ID_usuario`        INT             NOT NULL COMMENT 'Técnico que realizó la visita',
    `fecha_visita`      DATE            NOT NULL,
    `motivo`            ENUM('Preventiva', 'Correctiva') NOT NULL DEFAULT 'Preventiva',
    `reporte_tecnico`   TEXT            NOT NULL COMMENT 'Descripción detallada de la intervención',
    `costo_visita`      DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT 'Costo total en CLP',
    `aplica_garantia`   TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '1 = cubierto por garantía',
    `fecha_creacion`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`ID_visita`),
    CONSTRAINT `fk_visita_impresora`
        FOREIGN KEY (`ID_impresora`) REFERENCES `impresoras` (`ID_impresora`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_visita_usuario`
        FOREIGN KEY (`ID_usuario`) REFERENCES `usuarios` (`ID_usuario`)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX `idx_visitas_fecha` (`fecha_visita`),
    INDEX `idx_visitas_motivo` (`motivo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Historial de visitas técnicas con reportes y costos';


-- ---------------------------------------------------------------
-- TABLA: costos_adicionales_visita
-- Desglose de costos adicionales por visita técnica.
-- Permite registrar piezas, insumos y horas extra individuales.
-- ---------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `costos_adicionales_visita` (
    `ID_costo_adicional` INT            NOT NULL AUTO_INCREMENT,
    `ID_visita`          INT            NOT NULL,
    `ID_suministro`      INT            DEFAULT NULL COMMENT 'Suministro/pieza utilizada (NULL si es mano de obra)',
    `descripcion`        VARCHAR(200)   NOT NULL COMMENT 'Descripción del costo adicional',
    `cantidad`           INT            NOT NULL DEFAULT 1,
    `costo_momento`      DECIMAL(10,2)  NOT NULL DEFAULT 0.00 COMMENT 'Costo unitario al momento de la visita',
    PRIMARY KEY (`ID_costo_adicional`),
    CONSTRAINT `fk_costoextra_visita`
        FOREIGN KEY (`ID_visita`) REFERENCES `visitas_tecnicas` (`ID_visita`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_costoextra_suministro`
        FOREIGN KEY (`ID_suministro`) REFERENCES `suministros` (`ID_suministro`)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Desglose de costos adicionales (piezas, insumos, horas) por visita';


-- Reactivar revisiones de claves foráneas
SET FOREIGN_KEY_CHECKS = 1;


-- ================================================================
-- 6. DATOS DE EJEMPLO (SEED DATA)
-- ================================================================

-- Clientes de ejemplo
INSERT IGNORE INTO `clientes` (`rut`, `razon_social`, `direccion`, `telefono`, `contacto`, `email_contacto`) VALUES
    ('76.111.222-3', 'Empresa ABC SpA',           'Av. Libertador 1234, Of. 501, Santiago',   '+56 9 8765 4321', 'Juan Pérez',      'contacto@empresaabc.cl'),
    ('76.333.444-5', 'Constructora XYZ Ltda.',    'Av. Industrial 5678, Piso 3, Las Condes',  '+56 9 7777 8888', 'María López',     'admin@constructoraxyz.cl'),
    ('76.555.666-7', 'SpA Logística Norte',       'Calle Bodega 901, Quilicura',              '+56 9 6666 5555', 'Pedro Rojas',     'info@logisticanorte.cl'),
    ('76.789.012-3', 'Clínica Salud Total',       'Av. Salud 2345, Providencia',             '+56 9 5555 4444', 'Ana García',      'ti@saludtotal.cl');

-- Usuarios de ejemplo (contraseña: demo1234 — hash bcrypt)
INSERT IGNORE INTO `usuarios` (`ID_cliente`, `ID_rol`, `nombre`, `email`, `password`) VALUES
    (NULL, 1, 'Admin Demo',       'admin@mps.cl',       '$2y$10$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'),
    (1,    2, 'Carlos Finanzas',  'finanzas@abc.cl',    '$2y$10$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'),
    (1,    3, 'Carlos Mendoza',   'carlos@abc.cl',      '$2y$10$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'),
    (3,    3, 'Ana Silva',        'ana@logistica.cl',    '$2y$10$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'),
    (1,    4, 'Pedro Rojas',      'pedro@freelance.cl',  '$2y$10$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX');

-- Departamentos de ejemplo
INSERT IGNORE INTO `departamentos` (`ID_cliente`, `nombre_departamento`) VALUES
    (1, 'Administración'), (1, 'Ventas'), (1, 'Contabilidad'), (1, 'Bodega'),
    (2, 'Oficina Central'), (2, 'Obra'), (2, 'RRHH'),
    (3, 'Despacho'), (3, 'Recepción'), (3, 'Bodega Central'),
    (4, 'Recepción'), (4, 'Laboratorio'), (4, 'Consultorio 1');

-- Suministros de ejemplo
INSERT IGNORE INTO `suministros` (`tipo`, `modelo_codigo`, `color`, `rendimiento_estimado`, `costo_unitario`, `stock_actual`, `stock_minimo`) VALUES
    ('Tóner',          'HP 59A CF259A',        'Negro',    3150,   45990,  12, 3),
    ('Tóner',          'HP 59X CF259X',        'Negro',    10000,  79990,  6,  2),
    ('Drum',           'HP CF232A',            'Negro',    23000,  89990,  3,  1),
    ('Fusor',          'HP RG5-7772',          NULL,       150000, 129990, 2,  1),
    ('Tóner',          'Brother TN-2420',      'Negro',    3000,   39990,  8,  3),
    ('Drum',           'Brother DR-2400',      'Negro',    15000,  69990,  4,  1),
    ('Tinta',          'Epson 112 Negro',      'Negro',    4500,   14990,  15, 5),
    ('Tinta',          'Epson 112 Cyan',       'Cyan',     7500,   14990,  10, 4),
    ('Tinta',          'Epson 112 Magenta',    'Magenta',  7500,   14990,  10, 4),
    ('Tinta',          'Epson 112 Amarillo',   'Amarillo', 7500,   14990,  10, 4),
    ('Kit Mantención', 'HP JetIntelligence Kit', NULL,    NULL,   45990,  1,  3),
    ('Fusor',          'Brother LT5300',       NULL,       100000, 99990,  1,  1);


-- ================================================================
-- CONSULTAS DE VERIFICACIÓN
-- ================================================================
-- DESCRIBE `clientes`;
-- DESCRIBE `roles`;
-- DESCRIBE `usuarios`;
-- DESCRIBE `departamentos`;
-- DESCRIBE `impresoras`;
-- DESCRIBE `suministros`;
-- DESCRIBE `cambio_suministros`;
-- DESCRIBE `historial_contadores`;
-- DESCRIBE `visitas_tecnicas`;
-- DESCRIBE `costos_adicionales_visita`;
-- SELECT COUNT(*) AS total_clientes FROM `clientes`;
-- SELECT COUNT(*) AS total_roles FROM `roles`;
-- SELECT COUNT(*) AS total_suministros FROM `suministros`;
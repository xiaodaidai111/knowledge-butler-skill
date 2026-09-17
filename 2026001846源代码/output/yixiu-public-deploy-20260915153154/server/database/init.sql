-- 设备检修知识检索与标准作业系统 - 数据库初始化
-- 主要初始化脚本请使用 schema.sql 和 equipment_maintenance_schema.sql
-- 此文件保留用于兼容性

CREATE DATABASE IF NOT EXISTS health_diet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE health_diet_db;

-- 设备信息表
CREATE TABLE IF NOT EXISTS equipment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    category VARCHAR(50),
    manufacturer VARCHAR(100),
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'normal',
    image VARCHAR(255)
);

-- 插入示例设备数据
INSERT INTO equipment (name, model, category, manufacturer, location, status, image) VALUES
('摩托车发动机总成', 'CG-125', '发动机', '本田', '维修车间A区', 'normal', '/static/equipment.png'),
('配电柜', 'ZK-320', '电气系统', '正泰', '配电室B区', 'warning', '/static/equipment.png'),
('液压千斤顶', 'YZ-50T', '液压系统', '上海液压', '工具房C区', 'normal', '/static/equipment.png'),
('万用表', 'UT61E', '检测工具', '优利德', '工具房C区', 'normal', '/static/equipment.png'),
('点火线圈', 'DLI-001', '发动机', 'NGK', '备件库', 'normal', '/static/equipment.png');

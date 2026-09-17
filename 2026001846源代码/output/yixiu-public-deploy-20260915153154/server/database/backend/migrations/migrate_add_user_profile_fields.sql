-- 添加用户资料缺失字段的迁移脚本
-- 执行时间: 2026-03-18

USE health_diet_db;

-- 添加缺失的用户资料字段
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS gender VARCHAR(10) DEFAULT '男' COMMENT '性别' AFTER avatar,
ADD COLUMN IF NOT EXISTS age INT DEFAULT NULL COMMENT '年龄' AFTER gender,
ADD COLUMN IF NOT EXISTS height DECIMAL(5,2) DEFAULT NULL COMMENT '身高(cm)' AFTER age,
ADD COLUMN IF NOT EXISTS weight DECIMAL(5,2) DEFAULT NULL COMMENT '体重(kg)' AFTER height,
ADD COLUMN IF NOT EXISTS bio TEXT DEFAULT NULL COMMENT '个人简介' AFTER weight,
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间' AFTER updated_at;

-- 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_gender ON users(gender);
CREATE INDEX IF NOT EXISTS idx_age ON users(age);

-- 验证字段是否添加成功
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT, 
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'health_diet_db' 
  AND TABLE_NAME = 'users'
  AND COLUMN_NAME IN ('gender', 'age', 'height', 'weight', 'bio', 'last_login_at')
ORDER BY ORDINAL_POSITION;

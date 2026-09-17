-- 检修人员联系人信息字段迁移
-- 为 users 表添加检修岗位信息字段，使个人中心与检修任务联系人系统对齐
-- 执行方式: mysql -u root -p health_diet_db < add_contact_fields.sql

-- 新增字段（IF NOT EXISTS 通过 PROCEDURE 或忽略错误实现）
-- 如果列已存在，ALTER TABLE 会报错 "Duplicate column name"，可安全忽略

ALTER TABLE users ADD COLUMN department VARCHAR(50) DEFAULT NULL COMMENT '所属部门';
ALTER TABLE users ADD COLUMN position VARCHAR(50) DEFAULT NULL COMMENT '岗位（电气检修/发动机检修/质检验收等）';
ALTER TABLE users ADD COLUMN specialty VARCHAR(100) DEFAULT NULL COMMENT '擅长方向（配电柜/温升异常/端子排查等）';
ALTER TABLE users ADD COLUMN skill_level VARCHAR(30) DEFAULT NULL COMMENT '技能等级（初级/中级/高级技师等）';
ALTER TABLE users ADD COLUMN certifications VARCHAR(200) DEFAULT NULL COMMENT '资质证书';
ALTER TABLE users ADD COLUMN employee_id VARCHAR(30) DEFAULT NULL COMMENT '工号';

-- 为已有用户更新示例数据（可选，仅用于演示）
-- UPDATE users SET department='电气检修部', position='电气检修', specialty='配电柜、温升异常、端子排查', employee_id='MX-2026-001' WHERE id=1;

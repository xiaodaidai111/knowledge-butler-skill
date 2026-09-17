-- 修复触发器语法
USE health_diet_db;

-- 删除旧的触发器（如果存在）
DROP TRIGGER IF EXISTS update_last_login;

-- 创建新的触发器
DELIMITER //
CREATE TRIGGER update_last_login 
AFTER INSERT ON login_history
FOR EACH ROW
BEGIN
    IF NEW.status = 'success' THEN
        UPDATE users SET last_login_at = NEW.login_time WHERE id = NEW.user_id;
    END IF;
END//
DELIMITER ;

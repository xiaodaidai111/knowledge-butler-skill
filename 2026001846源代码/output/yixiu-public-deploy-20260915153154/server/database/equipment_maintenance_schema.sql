-- 设备检修知识检索与标准作业系统 - 核心表结构
-- 在现有 health_diet_db 基础上新增设备检修相关表

USE health_diet_db;

-- ============================================================
-- 1. 设备信息表
-- ============================================================
CREATE TABLE IF NOT EXISTS equipment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '设备名称',
    model VARCHAR(100) COMMENT '设备型号',
    category VARCHAR(50) COMMENT '设备分类（发动机/电气系统/传动系统/制动系统等）',
    manufacturer VARCHAR(100) COMMENT '制造商',
    location VARCHAR(255) COMMENT '安装位置',
    status ENUM('normal', 'warning', 'fault', 'offline', 'maintenance') DEFAULT 'normal' COMMENT '设备状态',
    install_date DATE COMMENT '安装日期',
    last_maintenance_date DATE COMMENT '最近维护日期',
    next_maintenance_date DATE COMMENT '下次维护日期',
    maintenance_cycle_days INT DEFAULT 90 COMMENT '维护周期（天）',
    spec_params JSON COMMENT '技术参数（JSON格式）',
    image VARCHAR(255) COMMENT '设备图片',
    qr_code VARCHAR(255) COMMENT '设备二维码',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_model (model),
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_next_maintenance (next_maintenance_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备信息表';

-- ============================================================
-- 2. 检修记录表（替代 health_records）
-- ============================================================
CREATE TABLE IF NOT EXISTS maintenance_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '检修人员ID',
    equipment_id INT COMMENT '设备ID',
    record_type ENUM('routine', 'fault_repair', 'emergency', 'inspection', 'overhaul') DEFAULT 'routine' COMMENT '检修类型',
    title VARCHAR(200) NOT NULL COMMENT '检修标题',
    description TEXT COMMENT '故障现象/检修内容描述',
    fault_code VARCHAR(50) COMMENT '故障代码',
    fault_category VARCHAR(50) COMMENT '故障分类',
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium' COMMENT '严重程度',
    status ENUM('pending', 'in_progress', 'completed', 'verified', 'rejected') DEFAULT 'pending' COMMENT '状态',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    duration_minutes INT COMMENT '耗时（分钟）',
    tools_used JSON COMMENT '使用的工具清单',
    parts_replaced JSON COMMENT '更换的零部件',
    safety_measures JSON COMMENT '安全措施（停电验电/挂牌上锁等）',
    before_images JSON COMMENT '检修前图片',
    after_images JSON COMMENT '检修后图片',
    compliance_score INT DEFAULT 0 COMMENT '合规评分（0-100）',
    quality_score INT DEFAULT 0 COMMENT '质量评分（0-100）',
    reviewer_id INT COMMENT '审核人ID',
    review_comment TEXT COMMENT '审核意见',
    reviewed_at DATETIME COMMENT '审核时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_record_type (record_type),
    INDEX idx_status (status),
    INDEX idx_severity (severity),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检修记录表';

-- ============================================================
-- 3. 检修知识库表（知识沉淀）
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '知识标题',
    content TEXT NOT NULL COMMENT '知识内容',
    category VARCHAR(50) COMMENT '知识分类（手册/案例/流程/标准）',
    equipment_category VARCHAR(50) COMMENT '适用设备分类',
    equipment_model VARCHAR(100) COMMENT '适用设备型号',
    fault_type VARCHAR(50) COMMENT '故障类型',
    tags JSON COMMENT '标签',
    source VARCHAR(255) COMMENT '来源（手册名称/案例上传者等）',
    source_file VARCHAR(255) COMMENT '来源文件路径（PDF/文档等）',
    embedding_vector JSON COMMENT '知识嵌入向量（用于RAG检索）',
    view_count INT DEFAULT 0 COMMENT '浏览次数',
    use_count INT DEFAULT 0 COMMENT '被引用次数',
    rating DECIMAL(3,1) DEFAULT 0 COMMENT '评分',
    status ENUM('draft', 'pending_review', 'approved', 'archived') DEFAULT 'approved' COMMENT '状态',
    uploader_id INT COMMENT '上传者ID',
    reviewer_id INT COMMENT '审核者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_title (title),
    INDEX idx_category (category),
    INDEX idx_equipment_category (equipment_category),
    INDEX idx_fault_type (fault_type),
    INDEX idx_status (status),
    FULLTEXT INDEX ft_content (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检修知识库表';

-- ============================================================
-- 4. 标准作业流程表
-- ============================================================
CREATE TABLE IF NOT EXISTS standard_procedures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL COMMENT '流程名称',
    code VARCHAR(50) UNIQUE COMMENT '流程编号',
    equipment_category VARCHAR(50) COMMENT '适用设备分类',
    maintenance_level ENUM('level1', 'level2', 'level3', 'inspection', 'emergency') DEFAULT 'level1' COMMENT '检修等级',
    description TEXT COMMENT '流程描述',
    steps JSON NOT NULL COMMENT '作业步骤（JSON数组）',
    safety_requirements JSON COMMENT '安全要求清单',
    required_tools JSON COMMENT '所需工具清单',
    required_parts JSON COMMENT '可能需要的零部件',
    estimated_duration INT COMMENT '预计工时（分钟）',
    compliance_standards JSON COMMENT '合规标准引用',
    version VARCHAR(20) DEFAULT '1.0' COMMENT '版本号',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_by INT COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_code (code),
    INDEX idx_equipment_category (equipment_category),
    INDEX idx_maintenance_level (maintenance_level),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标准作业流程表';

-- ============================================================
-- 5. 检修评估表（替代 takeaway_analysis）
-- ============================================================
CREATE TABLE IF NOT EXISTS inspection_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '评估人ID',
    maintenance_record_id INT COMMENT '关联检修记录ID',
    equipment_id INT COMMENT '设备ID',
    overall_score INT DEFAULT 0 COMMENT '总评分（0-100）',
    safety_score INT DEFAULT 0 COMMENT '安全合规评分',
    quality_score INT DEFAULT 0 COMMENT '作业质量评分',
    efficiency_score INT DEFAULT 0 COMMENT '效率评分',
    documentation_score INT DEFAULT 0 COMMENT '文档记录评分',
    dimensions JSON COMMENT '评分维度详情',
    strengths JSON COMMENT '优点',
    improvements JSON COMMENT '改进建议',
    suggestions JSON COMMENT '整改建议',
    analysis_text TEXT COMMENT '综合分析文本',
    risk_level ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium' COMMENT '风险等级',
    status ENUM('draft', 'submitted', 'reviewed', 'archived') DEFAULT 'draft' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (maintenance_record_id) REFERENCES maintenance_records(id) ON DELETE SET NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_overall_score (overall_score),
    INDEX idx_risk_level (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检修评估报告表';

-- ============================================================
-- 6. 风险告警表
-- ============================================================
CREATE TABLE IF NOT EXISTS risk_alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_id INT COMMENT '关联设备ID',
    alert_type ENUM('maintenance_due', 'fault_detected', 'parameter_abnormal', 'safety_risk', 'manual') NOT NULL COMMENT '告警类型',
    level ENUM('info', 'warning', 'critical', 'emergency') DEFAULT 'warning' COMMENT '告警等级',
    title VARCHAR(200) NOT NULL COMMENT '告警标题',
    description TEXT COMMENT '告警详情',
    recommended_action TEXT COMMENT '建议处置措施',
    is_resolved TINYINT(1) DEFAULT 0 COMMENT '是否已处理',
    resolved_by INT COMMENT '处理人ID',
    resolved_at DATETIME COMMENT '处理时间',
    resolution_note TEXT COMMENT '处理说明',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_alert_type (alert_type),
    INDEX idx_level (level),
    INDEX idx_is_resolved (is_resolved),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风险告警表';

-- ============================================================
-- 7. 用户检修能力表（替代 user_preferences 饮食偏好）
-- ============================================================
CREATE TABLE IF NOT EXISTS user_maintenance_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    specialty VARCHAR(100) COMMENT '专业方向（机械/电气/液压等）',
    skill_level ENUM('beginner', 'intermediate', 'advanced', 'expert') DEFAULT 'beginner' COMMENT '技能等级',
    certifications JSON COMMENT '持有资质证书',
    equipment_specialties JSON COMMENT '擅长设备类型',
    total_maintenance_count INT DEFAULT 0 COMMENT '累计检修次数',
    average_score DECIMAL(5,2) DEFAULT 0 COMMENT '平均评分',
    custom_notes TEXT COMMENT '个人备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_profile (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户检修能力档案表';

-- ============================================================
-- 更新成就数据为设备检修相关
-- ============================================================
-- 清除旧的饮食/健康相关成就
DELETE FROM user_achievements;
DELETE FROM achievements;

-- 插入设备检修相关成就
INSERT INTO achievements (name, icon, description) VALUES
('初次检修', '🔧', '完成第一次设备检修记录'),
('连续七日', '🔥', '连续7天完成检修任务'),
('检修达人', '💪', '累计完成30次设备检修'),
('安全之星', '⭐', '连续10次检修安全合规评分满分'),
('故障猎手', '🔍', '成功排查并修复10个疑难故障'),
('知识贡献者', '📚', '向知识库贡献5篇检修案例'),
('标准执行者', '📋', '连续20次按标准流程完成检修'),
('质量标兵', '🏆', '检修质量评分连续5次达到90分以上');

-- ============================================================
-- 更新社区示例数据为设备检修相关
-- ============================================================
-- 清除旧的饮食/健康相关社区示例数据
DELETE FROM community_post_comments;
DELETE FROM community_post_likes;
DELETE FROM community_posts;
DELETE FROM community_members;
DELETE FROM communities;

-- 插入设备检修相关社区
INSERT INTO communities (name, description, category, creator_id, latitude, longitude, address, max_members, current_members, activity_score, join_type, tags) VALUES
('发动机检修技术交流', '分享发动机故障排查经验，交流检修技巧', 'mechanical', 1, 39.9042, 116.4074, '北京市朝阳区', 500, 128, 85.5, 'open', '["发动机", "机械", "检修"]'),
('电气系统维护', '电气设备故障诊断与维护经验分享', 'electrical', 1, 39.9142, 116.4174, '北京市海淀区', 300, 89, 72.3, 'approval', '["电气", "维护", "诊断"]'),
('标准作业推广', '推广标准化检修作业流程，提升作业质量', 'standard', 1, 39.9242, 116.4274, '北京市西城区', 400, 156, 91.2, 'open', '["标准", "流程", "质量"]'),
('安全生产交流', '安全生产经验分享，安全意识提升', 'safety', 1, 39.9342, 116.4374, '北京市东城区', 350, 203, 88.7, 'open', '["安全", "生产", "防护"]'),
('液压系统专修', '液压系统故障分析与检修案例分享', 'hydraulic', 1, 39.9442, 116.4474, '北京市丰台区', 250, 67, 65.8, 'approval', '["液压", "系统", "专修"]'),
('新手检修员成长', '新手入门指导，基础技能培训与答疑', 'training', 1, 39.9542, 116.4574, '北京市石景山区', 200, 145, 94.5, 'approval', '["新手", "培训", "成长"]'),
('检修工具评测', '检修工具推荐与使用心得分享', 'tools', 1, 39.9642, 116.4674, '北京市通州区', 300, 112, 78.9, 'open', '["工具", "评测", "推荐"]'),
('预防性维护', '预防性维护策略与计划管理交流', 'preventive', 1, 39.9742, 116.4774, '北京市大兴区', 400, 178, 82.4, 'open', '["预防", "维护", "计划"]');

-- 插入设备检修相关社区成员
INSERT INTO community_members (community_id, user_id, role, post_count, comment_count) VALUES
(1, 1, 'owner', 25, 156),
(1, 2, 'admin', 18, 89),
(1, 3, 'member', 5, 23),
(2, 1, 'owner', 12, 67),
(2, 4, 'admin', 8, 45),
(3, 1, 'owner', 30, 203),
(3, 5, 'moderator', 15, 112),
(4, 1, 'owner', 22, 178),
(5, 1, 'owner', 10, 56),
(6, 1, 'owner', 35, 245),
(7, 1, 'owner', 18, 134),
(8, 1, 'owner', 20, 167);

-- 插入设备检修相关帖子
INSERT INTO community_posts (community_id, user_id, title, content, category, view_count, like_count, comment_count) VALUES
(1, 1, '摩托车发动机异响排查经验总结', '近期处理了一例摩托车发动机异响故障，最终定位为气门间隙超标。分享完整的排查思路和检修步骤...', 'case', 523, 89, 34),
(1, 2, '点火系统常见故障及快速诊断方法', '整理了火花塞、点火线圈、ECU等点火系统常见故障的快速诊断流程，附带万用表检测方法', 'case', 312, 67, 23),
(2, 1, '配电柜过热故障检修案例', '分享一例ZK-320配电柜过热故障的检修过程，从发现到修复的完整记录', 'case', 456, 78, 31),
(3, 1, '二级检修标准作业流程分享', '分享摩托车发动机二级检修的标准作业流程，包含工具准备、安全措施、检修步骤和验收标准', 'standard', 678, 134, 56),
(4, 1, '检修作业安全防护要点', '总结了设备检修作业中的安全防护要点，包括停电验电、挂牌上锁、个人防护装备等', 'safety', 890, 203, 78),
(6, 1, '新手入门：万用表使用基础教程', '为新手检修员整理的万用表使用基础教程，从电压、电流、电阻测量到常见故障检测', 'training', 1234, 312, 145);

-- 更新社区帖子数
UPDATE communities SET post_count = (
    SELECT COUNT(*) FROM community_posts WHERE community_id = communities.id
);

-- ============================================================
-- 插入设备信息示例数据
-- ============================================================
INSERT INTO equipment (name, model, category, manufacturer, location, status, maintenance_cycle_days) VALUES
('摩托车发动机总成', 'CG-125', '发动机', '本田', '维修车间A区', 'normal', 90),
('配电柜', 'ZK-320', '电气系统', '正泰', '配电室B区', 'warning', 30),
('液压千斤顶', 'YZ-50T', '液压系统', '上海液压', '工具房C区', 'normal', 180),
('万用表', 'UT61E', '检测工具', '优利德', '工具房C区', 'normal', 365),
('点火线圈', 'DLI-001', '发动机', 'NGK', '备件库', 'normal', 180);

-- ============================================================
-- 插入标准作业流程示例数据
-- ============================================================
INSERT INTO standard_procedures (name, code, equipment_category, maintenance_level, description, steps, safety_requirements, required_tools, estimated_duration) VALUES
('摩托车发动机一级检修', 'SOP-ENG-001', '发动机', 'level1', '发动机基础检查与维护',
 '["1. 检查机油液位与品质", "2. 检查空气滤清器", "3. 检查火花塞状态", "4. 检查点火正时", "5. 检查燃油供给系统", "6. 检查冷却系统", "7. 启动测试与怠速调整"]',
 '["穿戴工作服和手套", "确保发动机已冷却", "远离明火"]',
 '["机油尺", "火花塞扳手", "万用表", "气缸压力表"]',
 60),
('摩托车发动机二级检修', 'SOP-ENG-002', '发动机', 'level2', '发动机深度检修与部件更换',
 '["1. 拆卸气缸头", "2. 测量气门间隙", "3. 检查气门密封性", "4. 检查活塞环状态", "5. 测量气缸磨损", "6. 更换密封垫", "7. 重新组装与调试", "8. 路试验证"]',
 '["穿戴全套防护装备", "断开蓄电池负极", "使用举升架固定车辆", "扭矩扳手按标准力矩紧固"]',
 '["气门间隙规", "扭矩扳手", "气缸量表", "气门研磨工具", "密封胶"]',
 180),
('点火系统检查', 'SOP-IGN-001', '发动机', 'inspection', '点火系统全面检查',
 '["1. 检查火花塞电极间隙", "2. 测量点火线圈电阻", "3. 检查高压线状态", "4. 检查点火正时", "5. 测试点火强度"]',
 '["注意高压电危险", "发动机熄火状态下操作"]',
 '["万用表", "火花塞间隙规", "正时灯"]',
 30);

-- ============================================================
-- 插入知识库示例数据
-- ============================================================
INSERT INTO knowledge_base (title, content, category, equipment_category, fault_type, tags, source, status) VALUES
('摩托车发动机异响故障排查指南', '发动机异响是常见的故障现象，可能由气门间隙过大、链条磨损、轴承损坏等原因引起。排查步骤：1.判断异响来源区域（上部/下部/前部/后部）；2.冷车与热车异响对比；3.使用听诊器定位具体部位；4.逐项检查可能原因。', '手册', '发动机', '异响', '["异响", "排查", "发动机", "气门"]', '摩托车发动机维修手册', 'approved'),
('点火系统故障快速诊断流程', '点火系统故障表现为启动困难、怠速不稳、动力不足等。诊断流程：1.检查火花塞是否有火花；2.测量点火线圈初级/次级线圈电阻；3.检查ECU信号输出；4.检查曲轴位置传感器。', '案例', '发动机', '点火故障', '["点火", "火花塞", "诊断", "ECU"]', '一线检修案例', 'approved'),
('配电柜过热故障检修标准流程', '配电柜过热可能由接触不良、过载、散热不良等原因引起。检修流程：1.断电并挂牌上锁；2.使用红外测温仪检测热点；3.检查接线端子紧固情况；4.检查断路器额定电流；5.清理散热通道；6.送电后持续监测温度。', '流程', '电气系统', '过热', '["配电柜", "过热", "电气", "安全"]', 'ZK-320维修手册', 'approved');

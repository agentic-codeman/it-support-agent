CREATE TABLE `t_user` (
    `id`           VARCHAR(20)  NOT NULL COMMENT '主键ID',
    `username`     VARCHAR(64)  NOT NULL COMMENT '用户名，唯一',
    `password`     VARCHAR(128) NOT NULL COMMENT '密码',
    `role`         VARCHAR(32)  NOT NULL COMMENT '角色：admin/user',
    `avatar`       VARCHAR(128)          DEFAULT NULL COMMENT '用户头像',
    `create_time`  DATETIME              DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`  DATETIME              DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`      TINYINT               DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

CREATE TABLE `t_conversation` (
    `id`              VARCHAR(20) NOT NULL COMMENT '主键ID',
    `conversation_id` VARCHAR(20) NOT NULL COMMENT '会话ID',
    `user_id`         VARCHAR(20) NOT NULL COMMENT '用户ID',
    `title`           VARCHAR(128) NOT NULL COMMENT '会话名称',
    `last_time`       DATETIME             DEFAULT NULL COMMENT '最近消息时间',
    `create_time`     DATETIME             DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     DATETIME             DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`         TINYINT              DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_conversation_user` (`conversation_id`, `user_id`),
    KEY `idx_user_time` (`user_id`, `last_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话列表';

CREATE TABLE `t_conversation_summary` (
    `id`              VARCHAR(20)      NOT NULL COMMENT '主键ID',
    `conversation_id` VARCHAR(20) NOT NULL COMMENT '会话ID',
    `user_id`         VARCHAR(20) NOT NULL COMMENT '用户ID',
    `last_message_id` VARCHAR(20) NOT NULL COMMENT '摘要最后消息ID',
    `content`         TEXT        NOT NULL COMMENT '会话摘要内容',
    `create_time`     DATETIME             DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     DATETIME             DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`         TINYINT              DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    KEY `idx_conv_user` (`conversation_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话摘要表（与消息表分离存储）';

CREATE TABLE `t_message` (
    `id`                VARCHAR(20)      NOT NULL COMMENT '主键ID',
    `conversation_id`   VARCHAR(20) NOT NULL COMMENT '会话ID',
    `user_id`           VARCHAR(20) NOT NULL COMMENT '用户ID',
    `role`              VARCHAR(16) NOT NULL COMMENT '角色：user/assistant',
    `content`           TEXT        NOT NULL COMMENT '消息内容',
    `create_time`       DATETIME             DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`       DATETIME             DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`           TINYINT              DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    KEY `idx_conversation_user_time` (`conversation_id`, `user_id`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话消息记录表';

CREATE TABLE `t_message_feedback` (
    `id`              VARCHAR(20)       NOT NULL COMMENT '主键ID',
    `message_id`      VARCHAR(20)       NOT NULL COMMENT '消息ID',
    `conversation_id` VARCHAR(20)  NOT NULL COMMENT '会话ID',
    `user_id`         VARCHAR(20)  NOT NULL COMMENT '用户ID',
    `vote`            TINYINT      NOT NULL COMMENT '投票 1：赞 -1：踩',
    `reason`          VARCHAR(255)          DEFAULT NULL COMMENT '反馈原因',
    `comment`         VARCHAR(1024)         DEFAULT NULL COMMENT '反馈评论',
    `create_time`     DATETIME  NOT NULL COMMENT '创建时间',
    `update_time`     DATETIME  NOT NULL COMMENT '更新时间',
    `deleted`         TINYINT     NOT NULL DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_msg_user` (`message_id`, `user_id`),
    KEY `idx_conversation_id` (`conversation_id`),
    KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话消息反馈表';

CREATE TABLE `t_sample_question` (
    `id`          VARCHAR(20)        NOT NULL COMMENT 'ID',
    `title`       VARCHAR(64)               DEFAULT NULL COMMENT '展示标题',
    `description` VARCHAR(255)              DEFAULT NULL COMMENT '描述或提示',
    `question`    VARCHAR(255) NOT NULL COMMENT '示例问题内容',
    `create_time` DATETIME          DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME          DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`     TINYINT             DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    KEY `idx_sample_question_deleted` (`deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='示例问题表';

CREATE TABLE `t_knowledge_base` (
    `id`              VARCHAR(20)       NOT NULL COMMENT '主键 ID',
    `name`            VARCHAR(128) NOT NULL COMMENT '知识库名称',
    `embedding_model` VARCHAR(64)  NOT NULL COMMENT '嵌入模型标识',
    `collection_name` VARCHAR(64) NOT NULL COMMENT 'Collection名称',
    `created_by`      VARCHAR(20)  NOT NULL COMMENT '创建人',
    `updated_by`      VARCHAR(20)          DEFAULT NULL COMMENT '修改人',
    `create_time`     DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`     DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`         TINYINT     NOT NULL DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_collection_name` (`collection_name`),
    KEY `idx_kb_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库表';

CREATE TABLE `t_knowledge_document` (
    `id`               VARCHAR(20)        NOT NULL COMMENT 'ID',
    `kb_id`            VARCHAR(20)        NOT NULL COMMENT '知识库ID',
    `doc_name`         VARCHAR(256)  NOT NULL COMMENT '文档名称',
    `enabled`          TINYINT       NOT NULL DEFAULT 1 COMMENT '是否启用 1：启用 0：禁用',
    `chunk_count`      INT           DEFAULT 0 COMMENT '分块数量',
    `file_url`         VARCHAR(1024) NOT NULL COMMENT '文件存储路径',
    `file_type`        VARCHAR(16)   NOT NULL COMMENT '文件类型',
    `file_size`        BIGINT               DEFAULT NULL COMMENT '文件大小（字节）',
    `status`           VARCHAR(16)   NOT NULL DEFAULT 'pending' COMMENT '状态：pending/running/success/failed',
    `created_by`       VARCHAR(20)   NOT NULL COMMENT '创建人',
    `updated_by`       VARCHAR(20)          DEFAULT NULL COMMENT '修改人',
    `create_time`      DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`      DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`          TINYINT      NOT NULL DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    KEY `idx_kb_id` (`kb_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档表';

CREATE TABLE `t_knowledge_chunk` (
    `id`           VARCHAR(20)      NOT NULL COMMENT 'ID',
    `kb_id`        VARCHAR(20)      NOT NULL COMMENT '知识库ID',
    `doc_id`       VARCHAR(20)      NOT NULL COMMENT '文档ID',
    `chunk_index`  INT         NOT NULL COMMENT '分块序号',
    `content`      TEXT        NOT NULL COMMENT '分块内容',
    `content_hash` VARCHAR(64)          DEFAULT NULL COMMENT '内容哈希',
    `char_count`   INT                  DEFAULT NULL COMMENT '字符数',
    `token_count`  INT                  DEFAULT NULL COMMENT 'Token数',
    `enabled`      TINYINT    NOT NULL DEFAULT 1 COMMENT '是否启用',
    `created_by`   VARCHAR(20) NOT NULL COMMENT '创建人',
    `updated_by`   VARCHAR(20)          DEFAULT NULL COMMENT '修改人',
    `create_time`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted`      TINYINT    NOT NULL DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    KEY `idx_doc_id` (`doc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档分块表';

CREATE TABLE `t_intent_node` (
    `id`                    VARCHAR(20)       NOT NULL COMMENT '自增主键',
    `kb_id`                 VARCHAR(20)           DEFAULT NULL COMMENT '知识库ID',
    `intent_code`           VARCHAR(64)  NOT NULL COMMENT '业务唯一标识',
    `name`                  VARCHAR(64)  NOT NULL COMMENT '展示名称',
    `level`                 TINYINT      NOT NULL COMMENT '层级 0：DOMAIN 1：CATEGORY 2：TOPIC',
    `parent_code`           VARCHAR(64)          DEFAULT NULL COMMENT '父节点标识',
    `description`           VARCHAR(512)         DEFAULT NULL COMMENT '语义描述',
    `examples`              TEXT                 DEFAULT NULL COMMENT '示例问题',
    `collection_name`       VARCHAR(128)         DEFAULT NULL COMMENT '关联的Collection名称',
    `kind`                  TINYINT      NOT NULL DEFAULT 0 COMMENT '类型 0：RAG知识库类 1：SYSTEM系统交互类',
    `create_by`             VARCHAR(20)          DEFAULT NULL COMMENT '创建人',
    `update_by`             VARCHAR(20)          DEFAULT NULL COMMENT '修改人',
    `create_time`           DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`           DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
    `deleted`               TINYINT     NOT NULL DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='意图树节点配置表';

CREATE TABLE `t_query_term_mapping` (
    `id`          VARCHAR(20)       NOT NULL COMMENT 'ID',
    `domain`      VARCHAR(64)           DEFAULT NULL COMMENT '领域',
    `source_term` VARCHAR(128) NOT NULL COMMENT '源词',
    `target_term` VARCHAR(128) NOT NULL COMMENT '目标词',
    `match_type`  TINYINT      NOT NULL DEFAULT 1 COMMENT '匹配类型 1：精确 2：模糊',
    `priority`    INT          NOT NULL DEFAULT 100 COMMENT '优先级',
    `enabled`     TINYINT      NOT NULL DEFAULT 1 COMMENT '是否启用',
    `remark`      VARCHAR(255)         DEFAULT NULL COMMENT '备注',
    `create_by`   VARCHAR(20)          DEFAULT NULL COMMENT '创建人',
    `update_by`   VARCHAR(20)          DEFAULT NULL COMMENT '修改人',
    `create_time` DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
    `deleted`     TINYINT     NOT NULL DEFAULT 0 COMMENT '是否删除 0：正常 1：删除',
    PRIMARY KEY (`id`),
    KEY `idx_domain` (`domain`),
    KEY `idx_source` (`source_term`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关键词归一化映射表';

CREATE TABLE t_support_ticket (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '工单主键ticket_id',
  ticket_no VARCHAR(32) NOT NULL COMMENT '工单编号',
  title VARCHAR(255) NOT NULL COMMENT '工单标题',
  problem_desc TEXT COMMENT '问题现象描述',
  root_cause TEXT COMMENT '根因分析',
  solution TEXT COMMENT '解决方案',
  submitter_no VARCHAR(64) NOT NULL COMMENT '工单提出人工号',
  assignee_no VARCHAR(64) COMMENT '工单受理人工号',
  create_time DATETIME COMMENT '提交时间',
  update_time DATETIME ON UPDATE CURRENT_TIMESTAMP COMMENT '工单更新时间',
  status TINYINT COMMENT '工单状态：0待受理,1处理中,2已关闭',
  INDEX idx_ticket_no(ticket_no),
  INDEX idx_status_update (status, update_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='技术支持工单表';
# Hermes 智能调度系统设计

## 概述

实现基于 Hermes 的智能任务调度系统，支持多平台多账号任务编排、资源管理、飞书端交互优化。

## 架构

```
飞书用户 → 飞书机器人 → Hermes（对话层 + 调度层）
                          ↓
                     本地任务队列（SQLite）
                          ↓
                     dzcz-merchant-ops（执行器）
```

## 核心组件

### 1. 任务队列（TaskQueue）

**位置：** Hermes 层

**职责：**
- 任务排队和优先级管理
- 任务状态追踪
- 持久化存储（SQLite）

**数据结构：**
```python
{
    "task_id": "uuid",
    "user_id": "飞书用户ID",
    "platform": "bilibili",
    "merchant_key": "test-account",
    "workflow_id": "bilibili.video.like",
    "inputs": {"video_url": "..."},
    "priority": 1,  # 1=高, 2=中, 3=低
    "status": "pending|running|completed|failed",
    "created_at": "2026-06-14T10:00:00",
    "started_at": null,
    "completed_at": null,
    "result": null,
    "error": null
}
```

### 2. 资源管理器（ResourceManager）

**位置：** Hermes 层

**职责：**
- 管理浏览器实例数量
- 登录态状态缓存
- 资源分配和释放

**配置：**
```python
MAX_BROWSER_INSTANCES = 3  # 最大浏览器实例数
LOGIN_STATE_TTL = 3600     # 登录态缓存时间（秒）
```

**逻辑：**
```python
def can_execute(task):
    # 1. 检查浏览器实例数
    if running_tasks >= MAX_BROWSER_INSTANCES:
        return False, "浏览器实例已满，请等待"

    # 2. 检查登录态
    login_state = get_login_state(task.profile_id)
    if login_state == "expired":
        return False, "登录态已过期，请重新登录"

    return True, "可以执行"
```

### 3. 调度器（Scheduler）

**位置：** Hermes 层

**职责：**
- 从队列取任务
- 检查资源可用性
- 分配任务给执行器
- 更新任务状态

**调度策略：**
```python
def schedule():
    # 1. 获取待执行任务（按优先级排序）
    pending_tasks = get_pending_tasks(order_by="priority")

    for task in pending_tasks:
        # 2. 检查资源
        can_run, reason = can_execute(task)
        if not can_run:
            continue

        # 3. 执行任务
        execute_task(task)
        break
```

### 4. 飞书交互层（FeishuAdapter）

**位置：** Hermes 层

**职责：**
- 消息格式化（卡片消息）
- 任务确认流程
- 状态通知
- 批量操作支持

**消息类型：**

#### 任务确认消息
```json
{
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "任务确认"},
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**平台：** Bilibili\n**账号：** test-account\n**任务：** 视频点赞\n**视频：** https://..."
                }
            },
            {
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "确认执行"}, "type": "primary"},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "取消"}, "type": "default"}
                ]
            }
        ]
    }
}
```

#### 任务状态消息
```json
{
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "任务执行中"},
            "template": "orange"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**任务ID：** abc123\n**状态：** 执行中\n**进度：** 2/5 步骤完成"
                }
            }
        ]
    }
}
```

#### 任务完成消息
```json
{
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "任务完成"},
            "template": "green"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**任务ID：** abc123\n**状态：** 成功\n**结果：** 点赞成功 (89 → 90)"
                }
            },
            {
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "查看截图"}, "type": "default"},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "查看日志"}, "type": "default"}
                ]
            }
        ]
    }
}
```

#### 批量操作消息
```json
{
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "批量任务"},
            "template": "blue"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**任务列表：**\n1. Bilibili A账号 点赞 - 待确认\n2. 美团 B店铺 回复 - 待确认\n3. 抖音 C账号 发布 - 待确认"
                }
            },
            {
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "全部确认"}, "type": "primary"},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "全部取消"}, "type": "default"}
                ]
            }
        ]
    }
}
```

### 5. 任务追踪器（TaskTracker）

**位置：** Hermes 层

**职责：**
- 记录任务执行历史
- 提供任务查询接口
- 生成任务报告

**查询接口：**
```python
# 查询用户的任务列表
def get_user_tasks(user_id, status=None, limit=10):
    pass

# 查询任务详情
def get_task_detail(task_id):
    pass

# 查询任务统计
def get_task_stats(user_id):
    pass
```

## 交互流程

### 单任务流程

```
1. 用户：给 A 账号点赞
2. Hermes：找到 A 账号，准备执行点赞，确认？
   [确认] [取消]
3. 用户：确认
4. Hermes：任务已提交，正在执行...
5. Hermes：任务完成，点赞成功 (89 → 90)
   [查看截图] [查看日志]
```

### 批量任务流程

```
1. 用户：给 A 账号点赞，给 B 店铺回复
2. Hermes：
   **任务列表：**
   1. Bilibili A账号 点赞 - 待确认
   2. 美团 B店铺 回复 - 待确认
   [全部确认] [全部取消]
3. 用户：全部确认
4. Hermes：任务已提交，正在排队...
5. Hermes：任务 1/2 完成，A账号点赞成功
6. Hermes：任务 2/2 完成，B店铺回复成功
```

### 异常处理流程

```
1. Hermes：任务执行失败
   **错误：** 登录态已过期
   **建议：** 请重新登录 A 账号
   [重新登录] [查看截图]
2. 用户：重新登录
3. Hermes：已打开浏览器，请手动登录
4. 用户：登录完成
5. Hermes：登录成功，是否继续执行任务？
   [继续执行] [取消]
```

## 约束处理

### 飞书 API 限制
- 消息发送频率：每秒最多 5 条
- 卡片消息大小：最大 30KB
- 解决方案：消息队列 + 限流

### 浏览器资源
- 最大实例数：3（可配置）
- 解决方案：资源管理器控制并发

### 任务超时
- 默认超时：5 分钟
- 可配置：每个任务单独设置
- 解决方案：超时自动取消 + 通知用户

### 并发用户
- 支持：10+ 用户同时使用
- 解决方案：任务队列 + 优先级调度

## 文件结构

```
dzcz_merchant_ops/
├── hermes/
│   ├── __init__.py
│   ├── task_queue.py      # 任务队列
│   ├── resource_manager.py # 资源管理器
│   ├── scheduler.py        # 调度器
│   ├── feishu_adapter.py   # 飞书交互层
│   └── task_tracker.py     # 任务追踪器
├── cli.py                  # 现有 CLI
└── ...
```

## 实现阶段

### Phase 1：核心调度（本次实现）
- [ ] 任务队列（SQLite）
- [ ] 资源管理器
- [ ] 调度器
- [ ] CLI 集成

### Phase 2：飞书交互（后续）
- [ ] 消息格式化
- [ ] 确认流程
- [ ] 状态通知
- [ ] 批量操作

### Phase 3：优化增强（后续）
- [ ] 任务追踪
- [ ] 异常处理
- [ ] 性能优化

## 测试环境

- Python: E:\anaconda\envs\Hermes
- 测试框架: pytest
- 数据库: SQLite

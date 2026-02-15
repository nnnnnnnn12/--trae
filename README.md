# 美味到家 (Delicious Delivery) - Python 外卖平台

这是一个基于 Python Flask 开发的全功能外卖配送平台原型。支持用户下单、商家管理、评价系统、投诉监管机制以及**实时地理位置测距**。

## 🌟 核心功能

### 👤 用户端 (Customer)
- **浏览店铺**：查看 20+ 家不同品类的优质店铺（披萨、汉堡、寿司、中餐等）。
- **实时测距**：系统自动获取用户当前地理位置，并实时计算与店铺（初始设在**江西省新余市**）之间的物理距离（基于 Haversine 公式）。
- **智能图片**：商品配备高质量美食图片，并具备加载失败自动修复功能。
- **在线点餐**：选择心仪商品并一键下单。
- **订单管理**：
  - 查看历史订单状态（待处理、已完成、已退款、已投诉）。
  - **申请退款**：待处理订单支持一键退款。
  - **订单评价**：已完成订单可进行星级评价和文字评论。
  - **投诉商家**：对服务不放心的订单可发起投诉。

### 👨‍🍳 商家端 (Merchant)
- **经营仪表盘**：实时查看总订单数、累计收入和**累计投诉量**。
- **投诉监管**：若店铺累计投诉达 **3次**，系统将自动注销该店铺，保护消费者权益。
- **商品管理**：自主上架新商品，或随时下架（隐藏）已有商品。
- **订单处理**：实时接收用户订单并标记为“已完成”。
- **评价反馈**：在订单列表中直接查看用户给予的真实评价。

## 🛠️ 技术栈
- **后端**: Python 3.11 + Flask
- **数据库**: PostgreSQL (生产环境) / SQLite (开发环境) + SQLAlchemy ORM
- **认证**: Flask-Login (支持角色权限区分)
- **前端**: Jinja2 + CSS3 (Grid 布局) + JavaScript (Haversine 测距算法)
- **生产服务器**: Gunicorn

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/nnnnnnnn12/--trae.git
cd trae-test-python
```

### 2. 创建虚拟环境并安装依赖
```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 运行项目
```bash
python app.py
```
访问地址: `http://127.0.0.1:5000`

### 4. 测试账号
- **用户**: `customer` / `123456`
- **商家**: `merchant1` / `123456` (商家编号 1-24 均可)

## 📦 部署说明
项目已针对 **Render** 进行优化，包含 `Procfile` 和自动化的数据库初始化脚本。

- **环境变量配置**:
  - `SECRET_KEY`: 必须设置，用于加密 Session。
  - `DATABASE_URL`: 推荐连接 PostgreSQL 数据库。

## 📄 开源协议
MIT License

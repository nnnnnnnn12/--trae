# 美味到家 (Delicious Delivery) - Python 外卖平台

这是一个基于 Python Flask 开发的全功能外卖配送平台原型。支持用户下单、商家管理、评价系统以及投诉监管机制。

## 🌟 核心功能

### 👤 用户端 (Customer)
- **浏览店铺**：查看 20+ 家不同品类的优质店铺（披萨、汉堡、寿司、中餐等）。
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
- **数据库**: SQLite (SQLAlchemy ORM)
- **认证**: Flask-Login (支持角色权限区分)
- **前端**: Jinja2 模板引擎 + CSS3 (Flexbox/Grid) + JavaScript (图片容错处理)
- **生产服务器**: Gunicorn

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <your-repository-url>
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
项目已预配置好生产环境所需的 `Procfile` 和 `requirements.txt`。推荐部署至 **Render** 或 **PythonAnywhere**。

- **环境变量配置**:
  - `SECRET_KEY`: 用于加密 Session 的随机字符串。
  - `DATABASE_URL`: (可选) 连接外部 PostgreSQL 数据库的链接。

## 📄 开源协议
MIT License

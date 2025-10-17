# Flask Backend

这是一个简单的 Flask 后端 API 服务。

## 安装依赖

确保您已经激活了虚拟环境，然后运行：

```bash
cd backend
pip install -r requirements.txt
```

## 运行服务

```bash
python app.py
```

服务将在 `http://localhost:5555` 上运行。

## API 端点

- `GET /` - 欢迎页面
- `GET /api/health` - 健康检查
- `GET /api/data` - 获取示例数据
- `POST /api/data` - 提交数据

## 开发模式

应用默认以调试模式运行，文件修改后会自动重载。

# 数据预处理架构说明

## 架构设计原则

**前后端分离**：所有数据处理和计算逻辑放在后端，前端仅负责 UI 交互和数据展示。

## 后端架构

### 目录结构

```
backend/
├── preprocessing/           # 预处理模块
│   ├── __init__.py         # 模块导出
│   └── smoothing.py        # 数据平滑方法
├── routes/
│   ├── data_management.py  # 数据管理 API
│   └── preprocessing.py    # 预处理 API
└── app.py                  # 主应用
```

### 预处理模块设计

#### 1. 方法组织原则

- **按功能类型分文件**：每种预处理方法类型单独一个文件
  - `smoothing.py`：数据平滑（包含移动平均、指数、高斯等算法）
  - 未来可扩展：`detrending.py`、`normalization.py` 等

- **方法作为参数**：同类型的不同算法作为方法的参数选项
  - 例如：DataSmoothing 类支持 `method` 参数选择 'moving_average'、'exponential'、'gaussian'

#### 2. DataSmoothing 类

```python
class DataSmoothing:
    SUPPORTED_METHODS = ['moving_average', 'exponential', 'gaussian']
    
    @staticmethod
    def apply(values, method='moving_average', window_size=5)
    
    @staticmethod
    def get_method_info()  # 返回方法元信息
```

**支持的平滑算法**：

1. **移动平均（Moving Average）**
   - 简单滑动窗口平均
   - 适用于去除高频噪声
   - 参数：window_size（窗口大小）

2. **指数平滑（Exponential Smoothing）**
   - 指数加权移动平均
   - 对近期数据赋予更高权重
   - 参数：window_size（影响平滑程度）

3. **高斯平滑（Gaussian Smoothing）**
   - 基于高斯分布的加权平均
   - 提供更平滑的结果
   - 参数：window_size（影响平滑范围）

#### 3. 计算实现

- 使用 **NumPy** 进行高效数组计算
- 边界处理：自动处理数组边界情况
- 类型安全：输入输出均为 List[float]

### API 设计

#### 端点列表

1. **GET /api/preprocessing/methods**
   - 获取所有支持的预处理方法信息
   - 返回方法名称、描述、参数定义

2. **POST /api/preprocessing/smooth**
   - 应用单个平滑方法
   - 请求体：timestamps, values, method, window_size
   - 返回：处理后的 timestamps 和 values

3. **POST /api/preprocessing/apply-pipeline**
   - 应用预处理流程（多个方法按顺序执行）
   - 请求体：timestamps, values, methods[]
   - 返回：经过所有处理步骤后的数据

#### 流程处理逻辑

```python
# 依次应用每个预处理方法
processed_values = values
for method_config in methods:
    if method_config['type'] == 'smooth':
        processed_values = DataSmoothing.apply(
            processed_values,
            method=method_config['params']['method'],
            window_size=method_config['params']['window_size']
        )
```

## 前端架构

### DataPreprocessing 组件

**职责**：
- UI 交互：添加/删除/排序预处理方法
- API 调用：发送数据到后端进行处理
- 数据可视化：展示原始数据和处理后数据的对比

**不负责**：
- ❌ 数据计算和处理逻辑
- ❌ 算法实现

### 数据流

```
用户操作 → 前端状态更新 → 调用后端 API → 后端计算 → 返回结果 → 前端展示
```

### API 调用示例

```typescript
const response = await fetch('http://localhost:5555/api/preprocessing/apply-pipeline', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    timestamps: detectionData.timestamps,
    values: detectionData.values,
    methods: [
      {
        type: 'smooth',
        params: {
          method: 'moving_average',
          window_size: 5
        }
      }
    ]
  }),
});
```

## 扩展性设计

### 添加新的预处理方法

1. **创建新的方法文件**
   ```
   backend/preprocessing/detrending.py
   ```

2. **实现方法类**
   ```python
   class Detrending:
       SUPPORTED_METHODS = ['linear', 'polynomial']
       
       @staticmethod
       def apply(values, method='linear', **params):
           # 实现去趋势算法
           pass
       
       @staticmethod
       def get_method_info():
           # 返回方法元信息
           pass
   ```

3. **在 __init__.py 中导出**
   ```python
   from .detrending import Detrending
   __all__ = ['DataSmoothing', 'Detrending']
   ```

4. **在 API 路由中添加处理**
   ```python
   elif method_type == 'detrend':
       processed_values = Detrending.apply(processed_values, **params)
   ```

5. **前端添加 UI 支持**（无需修改计算逻辑）

### 优势

✅ **后端集中管理**：所有算法实现在后端，便于维护和优化  
✅ **前端轻量化**：前端代码简洁，专注于 UI 交互  
✅ **易于测试**：后端算法可独立测试，无需依赖前端  
✅ **性能优化**：可在后端使用高效的数值计算库（NumPy）  
✅ **安全性**：算法实现细节不暴露给前端  
✅ **可复用**：后端 API 可被其他客户端调用

## 依赖管理

### 后端依赖

```
Flask==3.0.0           # Web 框架
flask-cors==5.0.0      # 跨域支持
python-dotenv==1.0.0   # 环境变量
numpy>=1.26.0          # 数值计算
```

### 前端依赖

- 移除了前端的数值计算代码
- 仅保留 Plotly.js 用于数据可视化
- 通过 fetch API 与后端通信

## 性能考虑

1. **批量处理**：使用 NumPy 向量化操作，避免 Python 循环
2. **流水线处理**：一次 API 调用完成所有预处理步骤
3. **数据传输**：JSON 格式传输时间序列数据
4. **缓存策略**：前端缓存处理结果，仅在方法或数据变化时重新请求

## 未来规划

- [ ] 添加更多预处理方法（去趋势、标准化、差分等）
- [ ] 支持预处理配置的保存和加载
- [ ] 添加预处理效果的统计指标
- [ ] 支持异步处理大数据集
- [ ] 添加方法参数的自动推荐

# 数据预处理调试日志

## 问题描述

1. ❌ 前端显示三个独立的平滑方法，而不是一个"数据平滑"方法
2. ❌ 应用平滑后，图表显示的数据与原始数据相同（未生效）

## 已完成的修复

### 1. UI 修复 ✅

**修改文件**: `frontend/app/components/DataPreprocessing.tsx`

**变更内容**:
- 添加"方法类型"下拉框（固定显示"数据平滑"）
- 将原来的方法选择改为"平滑算法"子选项
- 保持 `getMethodDisplayName` 函数显示完整信息

**UI 结构**:
```
添加预处理方法
├── 方法类型: [数据平滑] (禁用，仅显示)
├── 平滑算法: [移动平均/指数平滑/高斯平滑]
└── 窗口大小: [数值输入]
```

### 2. 添加调试日志 ✅

在关键位置添加了 `console.log`:

1. **API 请求前**:
   - 请求体的时间戳数量
   - 请求体的值数量  
   - 方法数量和详情

2. **API 响应后**:
   - 完整响应结果
   - 原始数据长度
   - 处理后数据长度

3. **绘图数据生成时**:
   - detectionData 长度
   - processedData 长度
   - methods 数量
   - traces 数量

## 测试步骤

### 后端 API 测试 ✅

```bash
curl -X POST http://localhost:5555/api/preprocessing/apply-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "timestamps": ["2024-01-01 00:00:00", "2024-01-01 01:00:00", "2024-01-01 02:00:00"],
    "values": [1.0, 5.0, 2.0],
    "methods": [{
      "type": "smooth",
      "params": {
        "method": "moving_average",
        "window_size": 3
      }
    }]
  }'
```

**结果**: ✅ 成功
- 原始值: [1.0, 5.0, 2.0]
- 处理后: [3.0, 2.67, 3.5]
- 平滑生效！

### 前端测试计划

1. **打开浏览器** http://localhost:3333
2. **打开开发者工具控制台**
3. **选择数据文件** （从数据管理面板）
4. **查看控制台输出**:
   - 检查 TimeSettings 是否传递了 detectionData
   - 检查 DataPreprocessing 是否收到了数据

5. **添加预处理方法**:
   - 方法类型: 数据平滑
   - 平滑算法: 移动平均
   - 窗口大小: 5
   - 点击"应用方法"

6. **查看控制台输出**:
   ```
   === 预处理 Effect 触发 ===
   detectionData: XXX points
   methods: 1
   发送预处理请求: {...}
   预处理API响应: {...}
   原始数据长度: XXX
   处理后数据长度: XXX
   生成绘图数据 - detectionData: XXX processedData: XXX methods: 1
   添加处理后数据到图表: [...]
   生成的traces数量: 2
   ```

7. **检查图表**:
   - 应显示两条线：
     - 灰色：原始数据
     - 蓝色：处理后数据
   - 图例应显示"原始数据"和"处理后数据"
   - 两条线应该有明显差异

## 可能的问题和排查

### 问题 1: 图表只显示一条线

**检查**:
- 控制台日志中 `traces数量` 是否为 2
- `processedData` 长度是否 > 0
- `methods.length` 是否 > 0

**原因**:
```typescript
// 只有同时满足这两个条件才显示蓝色线
if (processedData.timestamps.length > 0 && methods.length > 0)
```

### 问题 2: 两条线完全重叠

**检查**:
- API 响应中的 values 是否与原始数据不同
- `setProcessedData` 是否被正确调用
- React 状态是否正确更新

**排查步骤**:
```javascript
// 在控制台手动比较
console.log('原始数据前5个:', detectionData.values.slice(0, 5));
console.log('处理后前5个:', processedData.values.slice(0, 5));
```

### 问题 3: API 请求失败

**检查**:
- 后端服务是否运行（http://localhost:5555）
- CORS 是否配置正确
- 请求格式是否正确

**排查**:
```bash
# 查看后端日志
tail -f /Users/bytedance/code/anomaly_detection_summary/backend.log
```

## 预期行为

### 无预处理方法时
- 左侧显示空列表
- 右侧图表显示：
  - 1 条灰色线（原始数据）
  - 图例只有"原始数据"

### 有预处理方法时
- 左侧显示方法列表
- 右侧图表显示：
  - 1 条灰色线（原始数据）
  - 1 条蓝色线（处理后数据）
  - 图例有"原始数据"和"处理后数据"
  - 蓝色线比灰色线更平滑

## 下一步

如果问题仍然存在：
1. 收集完整的控制台日志
2. 检查 Network 面板中的 API 请求和响应
3. 验证 React DevTools 中的组件状态
4. 确认 Plotly 的 revision 参数是否触发重绘

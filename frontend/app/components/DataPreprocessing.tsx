import { Typography, Button, Select, InputNumber, Input, Space, message, Empty } from "antd";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { useEffect, useState, useMemo } from "react";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const { Title, Text } = Typography;
const { Option } = Select;

// 可拖拽的流程项组件
interface SortableItemProps {
  id: string;
  index: number;
  method: PreprocessMethod;
  displayName: string;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

function SortableItem({ id, index, method, displayName, isSelected, onSelect, onDelete }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
    >
      <div
        style={{
          padding: "8px 12px",
          border: isSelected ? "1px solid #1890ff" : "1px solid #d9d9d9",
          borderRadius: "4px",
          marginBottom: "8px",
          backgroundColor: isSelected ? "#e6f7ff" : "#ffffff",
          transition: "all 0.3s",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div 
            style={{ flex: 1, cursor: "move" }}
            {...attributes}
            {...listeners}
          >
            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "4px" }}>
              步骤 {index + 1}
            </Text>
            <Text style={{ fontSize: "11px", color: "#595959" }}>
              {displayName}
            </Text>
          </div>
          <div style={{ display: "flex", gap: "4px", marginLeft: "8px" }}>
            <Button
              type="text"
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onSelect();
              }}
              style={{ padding: "2px 4px", fontSize: "12px" }}
            >
              编辑
            </Button>
            <Button
              type="text"
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              style={{ padding: "2px 4px" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// 预处理方法类型
type PreprocessMethod = {
  id: string;
  type: string;
  params: Record<string, any>;
};

// 参数定义
type ParamDefinition = {
  type: 'int' | 'float' | 'string' | 'select';
  default: any;
  min?: number;
  max?: number;
  options?: Array<{ label: string; value: any }>;
  description: string;
};

// 方法定义
type MethodDefinition = {
  name: string;
  description: string;
  params: Record<string, ParamDefinition>;
};

interface DataPreprocessingProps {
  selectedFile?: string;
  verticalRevision?: number;
  detectionData?: {
    timestamps: string[];
    values: number[];
  };
  onProcessedDataChange?: (data: { timestamps: string[]; values: number[] }) => void;
}

export default function DataPreprocessing({ 
  selectedFile, 
  verticalRevision, 
  detectionData,
  onProcessedDataChange 
}: DataPreprocessingProps) {
  const [Plot, setPlot] = useState<any>(null);
  const [revision, setRevision] = useState<number>(0);
  
  // 可用的预处理方法定义（从后端获取）
  const [availableMethods, setAvailableMethods] = useState<Record<string, MethodDefinition>>({});
  
  // 预处理方法流程
  const [methods, setMethods] = useState<PreprocessMethod[]>([]);
  
  // 当前选中的方法索引（用于编辑）
  const [selectedMethodIndex, setSelectedMethodIndex] = useState<number | null>(null);
  
  // 预处理后的数据
  const [processedData, setProcessedData] = useState<{
    timestamps: string[];
    values: number[];
  }>({ timestamps: [], values: [] });
  
  // 加载状态
  const [loading, setLoading] = useState<boolean>(false);
  
  // 当前正在编辑的方法（用于新增或修改）
  const [editingMethod, setEditingMethod] = useState<{
    type: string;
    params: Record<string, any>;
  }>({
    type: '',
    params: {},
  });

  // 辅助函数：根据类型获取方法定义
  const getMethodDefinition = (type: string): MethodDefinition | null => {
    return availableMethods[type] || null;
  };

  // 辅助函数：生成方法显示名称
  const getMethodDisplayName = (m: PreprocessMethod): string => {
    const methodDef = availableMethods[m.type];
    if (!methodDef) return '未知方法';
    
    const typeName = methodDef.name;
    
    // 生成参数描述
    const paramDesc = Object.entries(m.params)
      .map(([key, value]) => {
        const paramDef = methodDef.params[key];
        if (paramDef) {
          // 如果是 select 类型，显示对应的 label
          if (paramDef.type === 'select' && paramDef.options) {
            const option = paramDef.options.find(opt => opt.value === value);
            return option ? `${paramDef.description}=${option.label}` : `${paramDef.description}=${value}`;
          }
          return `${paramDef.description}=${value}`;
        }
        return `${key}=${value}`;
      })
      .join(', ');
    
    return `${typeName} (${paramDesc})`;
  };

  // 辅助函数：初始化方法的默认参数
  const getDefaultParams = (type: string): Record<string, any> => {
    const methodDef = getMethodDefinition(type);
    if (!methodDef) return {};
    
    const params: Record<string, any> = {};
    Object.entries(methodDef.params).forEach(([key, paramDef]) => {
      params[key] = paramDef.default;
    });
    return params;
  };

  // 辅助函数：渲染单个参数输入控件
  const renderParamInput = (paramKey: string, paramDef: ParamDefinition) => {
    const value = editingMethod.params[paramKey] ?? paramDef.default;
    
    const handleChange = (newValue: any) => {
      setEditingMethod({
        ...editingMethod,
        params: {
          ...editingMethod.params,
          [paramKey]: newValue,
        },
      });
    };

    switch (paramDef.type) {
      case 'int':
        return (
          <div key={paramKey}>
            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
              {paramDef.description}
            </Text>
            <InputNumber
              value={value}
              onChange={(v) => handleChange(v || paramDef.default)}
              min={paramDef.min}
              max={paramDef.max}
              size="middle"
              style={{ width: "100%" }}
            />
          </div>
        );
      
      case 'float':
        return (
          <div key={paramKey}>
            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
              {paramDef.description}
            </Text>
            <InputNumber
              value={value}
              onChange={(v) => handleChange(v || paramDef.default)}
              min={paramDef.min}
              max={paramDef.max}
              step={0.1}
              size="middle"
              style={{ width: "100%" }}
            />
          </div>
        );
      
      case 'select':
        return (
          <div key={paramKey}>
            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
              {paramDef.description}
            </Text>
            <Select
              value={value}
              onChange={handleChange}
              style={{ width: "100%" }}
              size="middle"
            >
              {paramDef.options?.map(opt => (
                <Option key={opt.value} value={opt.value}>{opt.label}</Option>
              ))}
            </Select>
          </div>
        );
      
      case 'string':
        return (
          <div key={paramKey}>
            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
              {paramDef.description}
            </Text>
            <Input
              value={value}
              onChange={(e) => handleChange(e.target.value)}
              size="middle"
              style={{ width: "100%" }}
            />
          </div>
        );
      
      default:
        return null;
    }
  };

  // 拖拽传感器
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // 从后端获取可用的预处理方法配置
  useEffect(() => {
    const fetchMethodTypes = async () => {
      try {
        const response = await fetch('http://localhost:5555/api/preprocessing/methods');
        const result = await response.json();
        
        if (result.success) {
          setAvailableMethods(result.data);
        } else {
          message.error('无法获取预处理方法配置');
        }
      } catch (error) {
        message.error('无法连接到后端服务');
      }
    };

    fetchMethodTypes();
  }, []);

  // 在客户端动态加载 Plotly
  useEffect(() => {
    import("react-plotly.js").then((module) => {
      setPlot(() => module.default);
    });
  }, []);

  // 当垂直方向拖拽时，更新 revision
  useEffect(() => {
    if (verticalRevision !== undefined && verticalRevision > 0) {
      setRevision(prev => prev + 1);
    }
  }, [verticalRevision]);

  // 当文件未选中时，清空预处理方法和数据
  useEffect(() => {
    if (!selectedFile) {
      setMethods([]);
      setProcessedData({ timestamps: [], values: [] });
    }
  }, [selectedFile]);

  // 当 processedData 变化时，通知父组件
  useEffect(() => {
    if (onProcessedDataChange) {
      onProcessedDataChange(processedData);
    }
  }, [processedData, onProcessedDataChange]);

  // 当检测数据或方法变化时，调用后端 API 应用预处理
  useEffect(() => {
    const applyPreprocessing = async () => {
      if (!detectionData || detectionData.timestamps.length === 0) {
        setProcessedData({ timestamps: [], values: [] });
        return;
      }

      if (methods.length === 0) {
        setProcessedData(detectionData);
        return;
      }

      try {
        setLoading(true);
        // 立即清空旧的处理数据，避免在加载新数据时显示旧数据
        setProcessedData({ timestamps: [], values: [] });
        
        // 构建请求体，前端参数直接发送给后端
        const requestBody = {
          timestamps: detectionData.timestamps,
          values: detectionData.values,
          methods: methods.map(m => ({
            type: m.type,
            params: m.params
          }))
        };
        
        const response = await fetch('http://localhost:5555/api/preprocessing/apply-pipeline', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        const result = await response.json();
        
        if (result.success) {
          setProcessedData(result.data);
        } else {
          message.error(result.message || '预处理失败');
          setProcessedData(detectionData);
        }
      } catch (error) {
        message.error('无法连接到后端服务');
        setProcessedData(detectionData);
      } finally {
        setLoading(false);
      }
    };

    applyPreprocessing();
  }, [detectionData, methods]);

  // 绘图数据 - 显示原始数据和处理后的数据
  const plotData = useMemo(() => {
    const traces = [];

    // 原始数据（灰色）
    if (detectionData && detectionData.timestamps.length > 0) {
      traces.push({
        x: detectionData.timestamps,
        y: detectionData.values,
        type: "scatter",
        mode: "lines",
        line: { color: "#d9d9d9", width: 1 },
        name: "原始数据",
        showlegend: true,
      });
    }

    // 处理后的数据（蓝色）- 只有在不加载中且有有效数据时才显示
    if (!loading && processedData.timestamps.length > 0 && methods.length > 0) {
      traces.push({
        x: processedData.timestamps,
        y: processedData.values,
        type: "scatter",
        mode: "lines",
        line: { color: "#1890ff", width: 2 },
        name: "处理后数据",
        showlegend: true,
      });
    }

    return traces;
  }, [detectionData, processedData, methods, loading]);

  // 处理拖拽结束
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setMethods((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);

        // 如果当前有选中的方法，更新选中索引
        if (selectedMethodIndex !== null) {
          if (selectedMethodIndex === oldIndex) {
            setSelectedMethodIndex(newIndex);
          } else if (selectedMethodIndex === newIndex) {
            setSelectedMethodIndex(oldIndex > newIndex ? selectedMethodIndex + 1 : selectedMethodIndex - 1);
          }
        }

        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  // 添加预处理方法
  const handleAddMethod = () => {
    if (!editingMethod.type) {
      message.warning('请先选择方法类型');
      return;
    }
    
    const newMethod: PreprocessMethod = {
      id: Date.now().toString(),
      type: editingMethod.type,
      params: { ...editingMethod.params },
    };
    setMethods([...methods, newMethod]);
    setSelectedMethodIndex(null);
    // 重置为空状态
    setEditingMethod({
      type: '',
      params: {},
    });
    message.success('已添加预处理方法');
  };

  // 更新选中的方法
  const handleUpdateMethod = () => {
    if (selectedMethodIndex === null) return;
    
    const updatedMethods = [...methods];
    updatedMethods[selectedMethodIndex] = {
      ...updatedMethods[selectedMethodIndex],
      type: editingMethod.type,
      params: { ...editingMethod.params },
    };
    setMethods(updatedMethods);
    
    // 退出编辑状态
    setSelectedMethodIndex(null);
    setEditingMethod({
      type: '',
      params: {},
    });
    
    message.success('已更新预处理方法');
  };

  // 删除方法
  const handleDeleteMethod = (id: string) => {
    const index = methods.findIndex(m => m.id === id);
    setMethods(methods.filter(m => m.id !== id));
    
    // 如果删除的是选中的方法，清除选中状态
    if (selectedMethodIndex === index) {
      setSelectedMethodIndex(null);
      setEditingMethod({
        type: '',
        params: {},
      });
    } else if (selectedMethodIndex !== null && selectedMethodIndex > index) {
      // 如果删除的方法在选中方法之前，更新选中索引
      setSelectedMethodIndex(selectedMethodIndex - 1);
    }
    
    message.success('已删除预处理方法');
  };

  // 选中某个方法进行编辑
  const handleSelectMethod = (index: number) => {
    setSelectedMethodIndex(index);
    const method = methods[index];
    setEditingMethod({
      type: method.type,
      params: { ...method.params },
    });
  };

  // 取消选中
  const handleCancelEdit = () => {
    setSelectedMethodIndex(null);
    setEditingMethod({
      type: '',
      params: {},
    });
  };

  return (
    <PanelGroup direction="horizontal" style={{ height: "100%" }}>
      {/* 左侧：预处理流程列表（可拖拽）+ 方法配置（左右分栏） */}
      <Panel defaultSize={30} minSize={25} maxSize={40}>
        <div style={{ 
          height: "100%", 
          display: "flex",
          flexDirection: "row",
          borderRight: "1px solid #f0f0f0",
        }}>
          {/* 左半部分：预处理流程列表 */}
          <div style={{ 
            flex: 1,
            padding: "12px", 
            overflowY: "auto", 
            display: "flex", 
            flexDirection: "column",
            borderRight: "1px solid #f0f0f0",
          }}>
            <div style={{ marginBottom: "12px" }}>
              <Title level={5} style={{ margin: 0, fontSize: "14px" }}>预处理流程</Title>
            </div>
            
            {selectedFile && detectionData && detectionData.timestamps.length > 0 ? (
              <>
                {methods.length === 0 ? (
                  <div style={{ 
                    flex: 1, 
                    display: "flex", 
                    justifyContent: "center", 
                    alignItems: "center", 
                    height: "100%" 
                  }}>
                    <p style={{ color: "#999" }}>暂无预处理方法</p>
                  </div>
                ) : (
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                  >
                    <SortableContext
                      items={methods.map(m => m.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      <div style={{ flex: 1, overflowY: "auto" }}>
                        {methods.map((method, index) => (
                          <SortableItem
                            key={method.id}
                            id={method.id}
                            index={index}
                            method={method}
                            displayName={getMethodDisplayName(method)}
                            isSelected={selectedMethodIndex === index}
                            onSelect={() => handleSelectMethod(index)}
                            onDelete={() => handleDeleteMethod(method.id)}
                          />
                        ))}
                      </div>
                    </SortableContext>
                  </DndContext>
                )}
              </>
            ) : (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <p style={{ color: "#999" }}>请先选择数据文件</p>
              </div>
            )}
          </div>

          {/* 右半部分：方法配置面板 */}
          <div style={{ 
            flex: 1,
            padding: "12px", 
            display: "flex",
            flexDirection: "column",
            overflow: "hidden"
          }}>
            <Title level={5} style={{ margin: 0, fontSize: "14px", flexShrink: 0, padding: "0 0 12px 0" }}>
              {selectedMethodIndex !== null ? '编辑预处理方法' : '添加预处理方法'}
            </Title>
            
            {selectedFile && detectionData && detectionData.timestamps.length > 0 ? (
              <div style={{ 
                display: "flex", 
                flexDirection: "column", 
                flex: 1,
                width: "100%",
                overflow: "hidden"
              }}>
                {/* 1. 方法类型选择 - 20% */}
                <div style={{ 
                  flex: "0 0 20%", 
                  borderBottom: "1px solid #f0f0f0"
                }}>
                  <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
                    方法类型
                  </Text>
                  <Select
                    value={editingMethod.type || undefined}
                    onChange={(value) => {
                      const params = getDefaultParams(value);
                      setEditingMethod({
                        type: value,
                        params,
                      });
                    }}
                    style={{ width: "100%" }}
                    size="middle"
                    showSearch
                    placeholder="请选择预处理方法类型"
                    allowClear
                  >
                    {Object.entries(availableMethods).map(([key, methodDef]) => (
                      <Option key={key} value={key}>{methodDef.name}</Option>
                    ))}
                  </Select>
                </div>
                
                {/* 2. 方法参数设置 - 中间可滚动区域 65% */}
                <div style={{ 
                  flex: "1 1 65%", 
                  overflowY: "auto",
                  borderBottom: "1px solid #f0f0f0"
                }}>
                  {editingMethod.type ? (() => {
                    const methodDef = getMethodDefinition(editingMethod.type);
                    if (!methodDef) return <Empty description="方法配置加载失败" />;
                    
                    return (
                      <Space direction="vertical" size="small" style={{ width: "100%" }}>
                        <div style={{ marginTop: "8px" }}>
                          <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
                            方法参数
                          </Text>
                        </div>
                        {Object.entries(methodDef.params).map(([key, paramDef]) => 
                          renderParamInput(key, paramDef)
                        )}
                      </Space>
                    );
                  })() : (
                    <div style={{ 
                      flex: 1, 
                      display: "flex", 
                      justifyContent: "center", 
                      alignItems: "center", 
                      height: "100%" 
                    }}>
                      <p style={{ color: "#999" }}>请先选择方法类型</p>
                    </div>
                  )}
                </div>
                
                {/* 3. 添加/更新按钮 - 15% */}
                <div style={{ 
                  flex: "0 0 15%", 
                  display: "flex",
                  alignItems: "center"
                }}>
                  {editingMethod.type && (
                    selectedMethodIndex !== null ? (
                      <div style={{ display: "flex", gap: "8px", width: "100%" }}>
                        <Button
                          type="primary"
                          onClick={handleUpdateMethod}
                          style={{ flex: 1 }}
                        >
                          更新参数
                        </Button>
                        <Button
                          onClick={handleCancelEdit}
                          style={{ flex: 1 }}
                        >
                          取消
                        </Button>
                      </div>
                    ) : (
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleAddMethod}
                        block
                      >
                        添加方法
                      </Button>
                    )
                  )}
                </div>
              </div>
            ) : (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <p style={{ color: "#999" }}>请先选择数据文件</p>
              </div>
            )}
          </div>
        </div>
      </Panel>
      
      <PanelResizeHandle style={{
        width: "2px",
        backgroundColor: "#f0f0f0",
        cursor: "col-resize",
      }} />
      
      {/* 右侧：预处理效果预览 */}
      <Panel defaultSize={70} minSize={50}>
        <div style={{ height: "100%", width: "100%", display: "flex", flexDirection: "column" }}>
          {selectedFile && detectionData && detectionData.timestamps.length > 0 ? (
            <>
              <div style={{ flex: 1, width: "100%", minHeight: 0 }}>
                {Plot && plotData.length > 0 ? (
                  <Plot
                    data={plotData}
                    layout={{
                      autosize: true,
                      margin: { l: 50, r: 20, t: 20, b: 50 },
                      xaxis: { 
                        title: undefined,
                        autorange: true,
                      },
                      yaxis: { 
                        title: undefined,
                        autorange: true,
                      },
                      showlegend: true,
                      legend: {
                        x: 0,
                        y: 1,
                        orientation: "h",
                        font: { size: 10 },
                      },
                      hovermode: "x unified",
                    }}
                    config={{
                      responsive: true,
                      displayModeBar: true,
                      displaylogo: false,
                    }}
                    style={{ width: "100%", height: "100%" }}
                    useResizeHandler={true}
                    revision={revision}
                  />
                ) : (
                  <div style={{ 
                    display: "flex", 
                    justifyContent: "center", 
                    alignItems: "center", 
                    height: "100%",
                    color: "#999",
                    fontSize: "12px",
                  }}>
                    暂无数据
                  </div>
                )}
              </div>
            </>
          ) : (
            <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
              <p style={{ color: "#999" }}>请在左侧数据管理中选择一个数据文件</p>
            </div>
          )}
        </div>
      </Panel>
    </PanelGroup>
  );
}

import { Typography, Button, Select, InputNumber, message, Empty } from "antd";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { useEffect, useState } from "react";
import { PlayCircleOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;
const { Option } = Select;

type ParamDefinition = {
  type: 'int' | 'float' | 'string' | 'select';
  default: any;
  min?: number;
  max?: number;
  step?: number;
  options?: Array<{ label: string; value: any }>;
  description: string;
  detail?: string;  // 参数详细说明
};

type MethodDefinition = {
  name: string;
  category?: string;  // 方法类型：统计型 or 距离型
  description: string;
  principle?: string;  // 检测原理
  params: Record<string, ParamDefinition>;
};

interface DetectionMethodSettingsProps {
  selectedFile?: string;
  verticalRevision?: number;
  detectionData?: {
    timestamps: string[];
    values: number[];
  };
}

export default function DetectionMethodSettings({ 
  selectedFile, 
  verticalRevision, 
  detectionData 
}: DetectionMethodSettingsProps) {
  const [PlotlyComponent, setPlotlyComponent] = useState<any>(null);
  const [revision, setRevision] = useState<number>(0);
  const [availableMethods, setAvailableMethods] = useState<Record<string, MethodDefinition>>({});
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedMethod, setSelectedMethod] = useState<{
    type: string;
    params: Record<string, any>;
  }>({
    type: '',
    params: {}
  });
  const [detectionResult, setDetectionResult] = useState<{
    timestamps: string[];
    values: number[];
    anomalies: boolean[];
    anomaly_indices: number[];
    stats: Record<string, any>;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    import("react-plotly.js").then((module) => {
      setPlotlyComponent(() => module.default);
    });
  }, []);

  useEffect(() => {
    if (verticalRevision !== undefined) {
      setRevision(verticalRevision);
    }
  }, [verticalRevision]);

  useEffect(() => {
    // 当文件变化时（包括切换到另一个文件），清空检测结果
    setDetectionResult(null);
    if (!selectedFile) {
      setSelectedCategory('');
      setSelectedMethod({ type: '', params: {} });
    }
  }, [selectedFile]);

  useEffect(() => {
    const fetchMethods = async () => {
      try {
        const response = await fetch('http://localhost:5555/api/detection/methods');
        const result = await response.json();
        
        if (result.success) {
          setAvailableMethods(result.data);
        } else {
          message.error('无法获取检测方法配置');
        }
      } catch (error) {
        message.error('无法连接到后端服务');
      }
    };
    fetchMethods();
  }, []);

  const getMethodDefinition = (type: string): MethodDefinition | null => {
    return availableMethods[type] || null;
  };

  const getDefaultParams = (type: string): Record<string, any> => {
    const methodDef = getMethodDefinition(type);
    if (!methodDef) return {};
    
    const params: Record<string, any> = {};
    Object.entries(methodDef.params).forEach(([key, paramDef]) => {
      params[key] = paramDef.default;
    });
    return params;
  };

  const renderParamInput = (paramKey: string, paramDef: ParamDefinition) => {
    const value = selectedMethod.params[paramKey] ?? paramDef.default;
    
    const handleChange = (newValue: any) => {
      setSelectedMethod({
        ...selectedMethod,
        params: {
          ...selectedMethod.params,
          [paramKey]: newValue,
        },
      });
    };

    switch (paramDef.type) {
      case 'int':
      case 'float':
        return (
          <div key={paramKey}>
            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "4px" }}>
              {paramDef.description}
            </Text>
            {paramDef.detail && (
              <Text style={{ fontSize: "10px", color: "#999", display: "block", marginBottom: "6px", lineHeight: "1.4" }}>
                {paramDef.detail}
              </Text>
            )}
            <InputNumber
              value={value}
              onChange={(v) => handleChange(v || paramDef.default)}
              min={paramDef.min}
              max={paramDef.max}
              step={paramDef.step || (paramDef.type === 'float' ? 0.1 : 1)}
              size="middle"
              style={{ width: "100%" }}
            />
          </div>
        );
      
      case 'select':
        return (
          <div key={paramKey}>
            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "4px" }}>
              {paramDef.description}
            </Text>
            {paramDef.detail && (
              <Text style={{ fontSize: "10px", color: "#999", display: "block", marginBottom: "6px", lineHeight: "1.4" }}>
                {paramDef.detail}
              </Text>
            )}
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
      
      default:
        return null;
    }
  };

  const handleApplyDetection = async () => {
    if (!selectedMethod.type) {
      message.warning('请先选择检测方法');
      return;
    }

    if (!detectionData || detectionData.timestamps.length === 0) {
      message.warning('没有可用的数据');
      return;
    }

    try {
      setLoading(true);
      const requestBody = {
        timestamps: detectionData.timestamps,
        values: detectionData.values,
        method: {
          type: selectedMethod.type,
          params: selectedMethod.params
        }
      };

      const response = await fetch('http://localhost:5555/api/detection/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      const result = await response.json();
      
      if (result.success) {
        setDetectionResult(result.data);
        message.success(`检测完成！发现 ${result.data.anomaly_indices.length} 个异常点`);
      } else {
        message.error(result.message || '检测失败');
      }
    } catch (error) {
      message.error('无法连接到后端服务');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PanelGroup direction="horizontal" style={{ height: "100%" }}>
      {/* 左侧：检测方法设置（左右分栏） */}
      <Panel defaultSize={30} minSize={20} maxSize={50}>
        <div style={{ 
          height: "100%", 
          display: "flex",
          flexDirection: "row",
          borderRight: "1px solid #f0f0f0",
        }}>
          {/* 左半部分：方法参数配置 */}
          <div style={{ 
            flex: 1,
            padding: "12px", 
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            borderRight: "1px solid #f0f0f0",
          }}>
            <Title level={5} style={{ margin: 0, fontSize: "14px", flexShrink: 0, padding: "0 0 12px 0" }}>方法参数配置</Title>
            
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
                }}>
                  <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
                    方法选择
                  </Text>
                  <div style={{ display: "flex", gap: "8px" }}>
                    {/* 方法类型选择器 */}
                    <div style={{ flex: 1 }}>
                      <Text style={{ fontSize: "11px", color: "#666", display: "block", marginBottom: "4px" }}>
                        方法类型
                      </Text>
                      <Select
                        value={selectedCategory || undefined}
                        onChange={(value) => {
                          setSelectedCategory(value);
                          // 清空当前选中的方法
                          setSelectedMethod({ type: '', params: {} });
                          setDetectionResult(null);
                        }}
                        placeholder="选择方法类型"
                        style={{ width: "100%" }}
                        size="middle"
                        allowClear
                      >
                        <Option value="统计型">统计型</Option>
                        <Option value="距离型">距离型</Option>
                      </Select>
                    </div>
                    
                    {/* 具体方法选择器 */}
                    <div style={{ flex: 1 }}>
                      <Text style={{ fontSize: "11px", color: "#666", display: "block", marginBottom: "4px" }}>
                        具体方法
                      </Text>
                      <Select
                        value={selectedMethod.type || undefined}
                        onChange={(value) => {
                          setSelectedMethod({
                            type: value,
                            params: getDefaultParams(value)
                          });
                          setDetectionResult(null);
                        }}
                        placeholder="选择检测方法"
                        style={{ width: "100%" }}
                        size="middle"
                        showSearch
                        allowClear
                        disabled={!selectedCategory}
                      >
                        {Object.entries(availableMethods)
                          .filter(([_, method]) => method.category === selectedCategory)
                          .map(([key, method]) => (
                            <Option key={key} value={key}>{method.name}</Option>
                          ))}
                      </Select>
                    </div>
                  </div>
              </div>

              {/* 2. 方法参数设置 - 中间可滚动区域 65% */}
              <div style={{ 
                flex: "1 1 65%", 
                overflowY: "auto",
                borderBottom: "1px solid #f0f0f0"
              }}>
                {selectedMethod.type && getMethodDefinition(selectedMethod.type) ? (
                  <div style={{ width: "100%", marginTop: "8px" }}>
                    {/* 参数设置 */}
                    <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
                      参数设置
                    </Text>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {Object.entries(getMethodDefinition(selectedMethod.type)!.params).map(([key, paramDef]) => 
                        renderParamInput(key, paramDef)
                      )}
                    </div>
                  </div>
                ) : (
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

              {/* 3. 应用按钮 - 15% */}
              <div style={{ 
                flex: "0 0 15%", 
                display: "flex",
                alignItems: "center"
              }}>
                {selectedMethod.type && (
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={handleApplyDetection}
                    loading={loading}
                    block
                  >
                    应用方法
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <p style={{ color: "#999" }}>请先选择数据文件</p>
            </div>
          )}
          </div>

          {/* 右半部分：检测结果统计 */}
          <div style={{ 
            flex: 1,
            padding: "12px", 
            display: "flex",
            flexDirection: "column",
            overflow: "hidden"
          }}>
            {selectedFile && detectionData && detectionData.timestamps.length > 0 ? (
              <div style={{ 
                flex: 1, 
                display: "flex", 
                flexDirection: "column", 
                overflow: "hidden"
              }}>
                {/* 上栏：方法简介 - 35% */}
                <div style={{ 
                  flex: "0 0 35%",
                  display: "flex",
                  flexDirection: "column",
                  overflow: "hidden"
                }}>
                  <Title level={5} style={{ margin: 0, fontSize: "14px", flexShrink: 0, padding: "0 0 8px 0" }}>
                    方法简介
                  </Title>
                  {selectedMethod.type && getMethodDefinition(selectedMethod.type) ? (
                    <div style={{ 
                      flex: 1,
                      overflowY: "auto",
                      padding: "12px",
                      backgroundColor: "#f5f5f5",
                      borderRadius: "4px",
                      borderLeft: "3px solid #1890ff"
                    }}>
                      <Text style={{ fontSize: "11px", color: "#666", display: "block", marginBottom: "4px" }}>
                        <strong>方法简介：</strong>
                      </Text>
                      <Text style={{ fontSize: "11px", color: "#333", lineHeight: "1.5", display: "block" }}>
                        {getMethodDefinition(selectedMethod.type)!.description}
                      </Text>
                      {getMethodDefinition(selectedMethod.type)!.principle && (
                        <>
                          <Text style={{ fontSize: "11px", color: "#666", display: "block", marginTop: "8px", marginBottom: "4px" }}>
                            <strong>检测原理：</strong>
                          </Text>
                          <Text style={{ fontSize: "11px", color: "#333", lineHeight: "1.5", display: "block" }}>
                            {getMethodDefinition(selectedMethod.type)!.principle}
                          </Text>
                        </>
                      )}
                    </div>
                  ) : (
                    <div style={{ 
                      flex: 1, 
                      display: "flex", 
                      justifyContent: "center", 
                      alignItems: "center",
                      backgroundColor: "#fafafa",
                      borderRadius: "4px",
                      border: "1px solid #f0f0f0"
                    }}>
                      <p style={{ color: "#999" }}>未选中方法</p>
                    </div>
                  )}
                </div>

                {/* 分隔符 */}
                <div style={{
                  height: "2px",
                  backgroundColor: "#f0f0f0",
                  margin: "12px 0",
                  flexShrink: 0
                }} />

                {/* 下栏：检测结果统计 */}
                <div style={{ 
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  overflow: "hidden"
                }}>
                  <Title level={5} style={{ margin: 0, fontSize: "14px", flexShrink: 0, padding: "0 0 8px 0" }}>
                    检测结果统计
                  </Title>
                  {detectionResult && detectionResult.stats ? (
                    <div style={{ 
                      flex: 1,
                      overflowY: "auto",
                      padding: "12px",
                      backgroundColor: "#fafafa",
                      borderRadius: "4px",
                      border: "1px solid #f0f0f0",
                      display: "flex",
                      flexDirection: "column",
                      gap: "12px",
                      fontSize: "12px"
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#666" }}>检测数据点数:</span>
                        <span style={{ fontWeight: 500 }}>{detectionResult.stats.total_points}</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <span style={{ color: "#666" }}>有效数据点数:</span>
                        <span style={{ fontWeight: 500 }}>{detectionResult.stats.valid_points}</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", color: "#ff4d4f" }}>
                        <span>异常数据点数:</span>
                        <span style={{ fontWeight: 600 }}>{detectionResult.stats.anomaly_count}</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", color: "#ff4d4f" }}>
                        <span>异常比例:</span>
                        <span style={{ fontWeight: 600 }}>{(detectionResult.stats.anomaly_ratio * 100).toFixed(2)}%</span>
                      </div>
                      {detectionResult.anomaly_indices.length > 0 && (
                        <>
                          <div style={{ borderTop: "1px solid #e0e0e0", marginTop: "4px", paddingTop: "8px" }}>
                            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px", color: "#ff4d4f" }}>
                              第一个异常点
                            </Text>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span style={{ color: "#666" }}>时间:</span>
                            <span style={{ fontWeight: 500, fontSize: "11px", wordBreak: "break-all" }}>
                              {detectionResult.timestamps[detectionResult.anomaly_indices[0]]}
                            </span>
                          </div>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span style={{ color: "#666" }}>数值:</span>
                            <span style={{ fontWeight: 500 }}>
                              {detectionResult.values[detectionResult.anomaly_indices[0]].toFixed(2)}
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                  ) : (
                    <div style={{ 
                      flex: 1, 
                      display: "flex", 
                      justifyContent: "center", 
                      alignItems: "center",
                      backgroundColor: "#fafafa",
                      borderRadius: "4px",
                      border: "1px solid #f0f0f0"
                    }}>
                      <p style={{ color: "#999" }}>点击"应用方法"查看结果</p>
                    </div>
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
      
      <Panel minSize={50}>
        <div style={{ height: "100%", width: "100%"}}>
          {!selectedFile || !detectionData || detectionData.timestamps.length === 0 ? (
            <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
              <p style={{ color: "#999" }}>请在左侧数据管理中选择一个数据文件</p>
            </div>
          ) : !detectionResult ? (
            <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
              <p style={{ color: "#999" }}>请选择检测方法并点击'应用方法'按钮查看检测结果</p>
            </div>
          ) : (
            <div style={{ height: "100%", width: "100%" }}>
              {PlotlyComponent && (
                <PlotlyComponent
                  key={revision}
                  data={[
                    {
                      x: detectionResult.timestamps,
                      y: detectionResult.values,
                      type: 'scatter',
                      mode: 'lines',
                      name: '原始数据',
                      line: { color: '#1890ff', width: 2 },
                    },
                    {
                      x: detectionResult.anomaly_indices.map(idx => detectionResult.timestamps[idx]),
                      y: detectionResult.anomaly_indices.map(idx => detectionResult.values[idx]),
                      type: 'scatter',
                      mode: 'markers',
                      name: '异常点',
                      marker: { 
                        color: '#ff4d4f', 
                        size: 5,
                        symbol: 'circle'
                      },
                    },
                  ]}
                  layout={{
                    autosize: true,
                    margin: { l: 50, r: 20, t: 20, b: 50 },
                    xaxis: { 
                      title: undefined,
                      type: 'date',
                      range: [detectionResult.timestamps[0], detectionResult.timestamps[detectionResult.timestamps.length - 1]],
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
                  style={{ width: "100%", height: "100%" }}
                  config={{
                    responsive: true,
                    displayModeBar: true,
                    displaylogo: false,
                  }}
                  useResizeHandler={true}
                />
              )}
            </div>
          )}
        </div>
      </Panel>
    </PanelGroup>
  );
}

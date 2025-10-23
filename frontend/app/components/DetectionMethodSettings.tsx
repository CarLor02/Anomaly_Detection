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
};

type MethodDefinition = {
  name: string;
  description: string;
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
    if (!selectedFile) {
      setSelectedMethod({ type: '', params: {} });
      setDetectionResult(null);
    }
  }, [selectedFile]);

  // 添加调试日志
  useEffect(() => {
    console.log('=== DetectionMethodSettings 状态 ===');
    console.log('selectedFile:', selectedFile);
    console.log('detectionData:', detectionData);
    console.log('detectionData?.timestamps.length:', detectionData?.timestamps.length);
    console.log('availableMethods:', Object.keys(availableMethods));
  }, [selectedFile, detectionData, availableMethods]);

  useEffect(() => {
    const fetchMethods = async () => {
      try {
        const response = await fetch('http://localhost:5555/api/detection/methods');
        const result = await response.json();
        
        if (result.success) {
          setAvailableMethods(result.data);
          console.log('已加载检测方法配置:', result.data);
        } else {
          message.error('无法获取检测方法配置');
        }
      } catch (error) {
        console.error('获取检测方法配置失败:', error);
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
            <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
              {paramDef.description}
            </Text>
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
      console.error('检测请求失败:', error);
      message.error('无法连接到后端服务');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PanelGroup direction="horizontal" style={{ height: "100%" }}>
      <Panel defaultSize={30} minSize={20} maxSize={50}>
        <div style={{ 
          height: "100%", 
          padding: "16px", 
          borderRight: "1px solid #f0f0f0", 
          display: "flex",
          flexDirection: "column",
          overflow: "hidden"
        }}>
          <Title level={5} style={{ margin: 0, fontSize: "14px", flexShrink: 0, padding: "0 0 12px 0" }}>检测方法设置</Title>
          
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
                  value={selectedMethod.type || undefined}
                  onChange={(value) => {
                    setSelectedMethod({
                      type: value,
                      params: getDefaultParams(value)
                    });
                    setDetectionResult(null);
                  }}
                  placeholder="请选择检测方法"
                  style={{ width: "100%" }}
                  size="middle"
                  showSearch
                  allowClear
                >
                  {Object.entries(availableMethods).map(([key, method]) => (
                    <Option key={key} value={key}>{method.name}</Option>
                  ))}
                </Select>
              </div>

              {/* 2. 方法参数设置 - 中间可滚动区域 65% */}
              <div style={{ 
                flex: "1 1 65%", 
                overflowY: "auto",
                borderBottom: "1px solid #f0f0f0"
              }}>
                {selectedMethod.type && getMethodDefinition(selectedMethod.type) ? (
                  <div style={{ width: "100%" }}>
                    <div style={{ marginTop: "8px" }}>
                      <Text strong style={{ fontSize: "12px", display: "block", marginBottom: "8px" }}>
                        方法参数
                      </Text>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {Object.entries(getMethodDefinition(selectedMethod.type)!.params).map(([key, paramDef]) => 
                        renderParamInput(key, paramDef)
                      )}
                    </div>
                  </div>
                ) : (
                  <Empty 
                    description="请先选择方法类型" 
                    style={{ marginTop: "40px" }}
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
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

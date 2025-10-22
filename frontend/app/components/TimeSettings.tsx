import { Typography, Spin, message, Slider, DatePicker, Space } from "antd";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { useEffect, useState, useMemo } from "react";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";

const { Title } = Typography;
const { RangePicker } = DatePicker;

interface TimeSettingsProps {
  selectedFile?: string;
  verticalRevision?: number;
}

export default function TimeSettings({ selectedFile, verticalRevision }: TimeSettingsProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [timestamps, setTimestamps] = useState<string[]>([]);
  const [values, setValues] = useState<number[]>([]);
  const [Plot, setPlot] = useState<any>(null);
  const [revision, setRevision] = useState<number>(0);
  
  // 时间范围状态
  const [timeRange, setTimeRange] = useState<[Dayjs | null, Dayjs | null]>([null, null]);
  const [sliderRange, setSliderRange] = useState<[number, number]>([0, 100]);

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

  useEffect(() => {
    if (selectedFile) {
      fetchFileData(selectedFile);
    } else {
      // 清空数据
      setTimestamps([]);
      setValues([]);
      setTimeRange([null, null]);
      setSliderRange([0, 100]);
    }
  }, [selectedFile]);

  // 当数据加载后，初始化时间范围为全部
  useEffect(() => {
    if (timestamps.length > 0) {
      const startTime = dayjs(timestamps[0]);
      const endTime = dayjs(timestamps[timestamps.length - 1]);
      setTimeRange([startTime, endTime]);
      setSliderRange([0, 100]);
    }
  }, [timestamps]);

  const fetchFileData = async (filePath: string) => {
    try {
      setLoading(true);
      console.log("Fetching file data for:", filePath);
      
      const response = await fetch(
        `http://localhost:5555/api/data/read-file?path=${encodeURIComponent(filePath)}`
      );
      
      console.log("Response status:", response.status);
      const result = await response.json();
      console.log("Response data:", result);

      if (result.success) {
        console.log("Data loaded successfully:", {
          timestamps: result.data.timestamps.length,
          values: result.data.values.length,
          fileType: result.data.file_type
        });
        setTimestamps(result.data.timestamps);
        setValues(result.data.values);
        message.success(`成功加载 ${result.data.total_points} 个数据点`);
      } else {
        console.error("Failed to load data:", result.message);
        message.error(result.message || "读取文件失败");
      }
    } catch (error) {
      console.error("Error fetching file data:", error);
      message.error("无法加载文件数据");
    } finally {
      setLoading(false);
    }
  };

  // 处理滑块变化
  const handleSliderChange = (value: number[]) => {
    if (timestamps.length === 0) return;
    
    setSliderRange(value as [number, number]);
    
    const totalPoints = timestamps.length;
    const startIndex = Math.floor((value[0] / 100) * (totalPoints - 1));
    const endIndex = Math.floor((value[1] / 100) * (totalPoints - 1));
    
    const startTime = dayjs(timestamps[startIndex]);
    const endTime = dayjs(timestamps[endIndex]);
    setTimeRange([startTime, endTime]);
  };

  // 处理日期选择器变化
  const handleDateChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    if (!dates || !dates[0] || !dates[1] || timestamps.length === 0) {
      return;
    }
    
    setTimeRange(dates);
    
    // 将日期转换为滑块百分比
    const startTime = dates[0].valueOf();
    const endTime = dates[1].valueOf();
    const dataStartTime = dayjs(timestamps[0]).valueOf();
    const dataEndTime = dayjs(timestamps[timestamps.length - 1]).valueOf();
    const totalDuration = dataEndTime - dataStartTime;
    
    const startPercent = Math.max(0, Math.min(100, ((startTime - dataStartTime) / totalDuration) * 100));
    const endPercent = Math.max(0, Math.min(100, ((endTime - dataStartTime) / totalDuration) * 100));
    
    setSliderRange([startPercent, endPercent]);
  };

  // 计算绘图数据 - 根据检测时间范围分段显示
  const plotData = useMemo(() => {
    if (timestamps.length === 0 || !timeRange[0] || !timeRange[1]) {
      return [];
    }

    const detectionStart = timeRange[0].valueOf();
    const detectionEnd = timeRange[1].valueOf();

    // 分为三段：前灰色、中间蓝色、后灰色
    const beforeDetection: { x: string[], y: number[] } = { x: [], y: [] };
    const duringDetection: { x: string[], y: number[] } = { x: [], y: [] };
    const afterDetection: { x: string[], y: number[] } = { x: [], y: [] };

    timestamps.forEach((ts, idx) => {
      const tsTime = dayjs(ts).valueOf();
      
      if (tsTime < detectionStart) {
        beforeDetection.x.push(ts);
        beforeDetection.y.push(values[idx]);
      } else if (tsTime <= detectionEnd) {
        duringDetection.x.push(ts);
        duringDetection.y.push(values[idx]);
      } else {
        afterDetection.x.push(ts);
        afterDetection.y.push(values[idx]);
      }
    });

    const traces = [];

    if (beforeDetection.x.length > 0) {
      traces.push({
        x: beforeDetection.x,
        y: beforeDetection.y,
        type: "scatter",
        mode: "lines",
        line: { color: "#d9d9d9" },
        name: "检测前",
        showlegend: false,
      });
    }

    if (duringDetection.x.length > 0) {
      traces.push({
        x: duringDetection.x,
        y: duringDetection.y,
        type: "scatter",
        mode: "lines",
        line: { color: "#1890ff", width: 2 },
        name: "检测范围",
        showlegend: false,
      });
    }

    if (afterDetection.x.length > 0) {
      traces.push({
        x: afterDetection.x,
        y: afterDetection.y,
        type: "scatter",
        mode: "lines",
        line: { color: "#d9d9d9" },
        name: "检测后",
        showlegend: false,
      });
    }

    return traces;
  }, [timestamps, values, timeRange]);

  // 计算边界虚线 - 当检测范围不等于数据范围时显示
  const boundaryShapes = useMemo(() => {
    if (timestamps.length === 0 || !timeRange[0] || !timeRange[1]) {
      return [];
    }

    const shapes = [];
    const dataStart = dayjs(timestamps[0]).valueOf();
    const dataEnd = dayjs(timestamps[timestamps.length - 1]).valueOf();
    const detectionStart = timeRange[0].valueOf();
    const detectionEnd = timeRange[1].valueOf();

    // 如果检测开始时间不等于数据开始时间，添加起始边界线
    if (detectionStart !== dataStart) {
      shapes.push({
        type: 'line',
        x0: timeRange[0].format('YYYY-MM-DD HH:mm:ss'),
        x1: timeRange[0].format('YYYY-MM-DD HH:mm:ss'),
        y0: 0,
        y1: 1,
        yref: 'paper',
        line: {
          color: '#000000',
          width: 1.5,
          dash: 'dash'
        }
      });
    }

    // 如果检测结束时间不等于数据结束时间，添加终止边界线
    if (detectionEnd !== dataEnd) {
      shapes.push({
        type: 'line',
        x0: timeRange[1].format('YYYY-MM-DD HH:mm:ss'),
        x1: timeRange[1].format('YYYY-MM-DD HH:mm:ss'),
        y0: 0,
        y1: 1,
        yref: 'paper',
        line: {
          color: '#000000',
          width: 1.5,
          dash: 'dash'
        }
      });
    }

    return shapes;
  }, [timestamps, timeRange]);

  return (
    <PanelGroup direction="horizontal" style={{ height: "100%" }}>
      <Panel defaultSize={30} minSize={20} maxSize={50} onResize={() => setRevision(prev => prev + 1)}>
        <div style={{ height: "100%", padding: "12px", borderRight: "1px solid #f0f0f0", overflowY: "auto" }}>
          <Title level={5} style={{ margin: "0 0 12px 0", fontSize: "14px" }}>检测时间设置</Title>
          
          {selectedFile && (
            <div style={{ marginBottom: "12px", fontSize: "11px", color: "#999" }}>
              <div style={{ wordBreak: "break-all", lineHeight: "1.4" }}>{selectedFile}</div>
            </div>
          )}
          
          {timestamps.length > 0 && (
            <Space direction="vertical" style={{ width: "100%" }} size="small">
              <div>
                <div style={{ marginBottom: "6px", fontSize: "12px", fontWeight: 500 }}>数据范围</div>
                <div style={{ fontSize: "11px", color: "#666", lineHeight: "1.8" }}>
                  <div style={{ display: "flex" }}>
                    <span style={{ flex: 1 }}>起始: {timestamps[0]}</span>
                    <span style={{ flex: 1 }}>终止: {timestamps[timestamps.length - 1]}</span>
                  </div>
                  <div style={{ marginTop: "2px" }}>共 {timestamps.length} 个数据点</div>
                </div>
              </div>

              <div style={{ marginTop: "8px" }}>
                <div style={{ marginBottom: "6px", fontSize: "12px", fontWeight: 500 }}>检测范围</div>
                <RangePicker
                  showTime
                  value={timeRange}
                  onChange={handleDateChange}
                  style={{ width: "100%" }}
                  size="small"
                  format="YYYY-MM-DD HH:mm"
                />
              </div>

              <div style={{ marginTop: "8px" }}>
                <Slider
                  range
                  value={sliderRange}
                  onChange={handleSliderChange}
                  tooltip={{ open: false }}
                />
              </div>
            </Space>
          )}
        </div>
      </Panel>
      <PanelResizeHandle style={{
        width: "2px",
        backgroundColor: "#f0f0f0",
        cursor: "col-resize",
      }} />
      <Panel minSize={50} onResize={() => setRevision(prev => prev + 1)}>
        <div style={{ height: "100%", width: "100%", display: "flex", flexDirection: "column" }}>
          {loading ? (
            <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
              <Spin tip="加载数据中..." />
            </div>
          ) : timestamps.length > 0 && Plot ? (
            <div style={{ flex: 1, width: "100%", height: "100%" }}>
              <Plot
                data={plotData}
                layout={{
                  autosize: true,
                  margin: { l: 50, r: 20, t: 20, b: 50 },
                  xaxis: {
                    autorange: true,
                  },
                  yaxis: {
                    autorange: true,
                  },
                  shapes: boundaryShapes,
                }}
                revision={revision}
                style={{ width: "100%", height: "100%" }}
                config={{ 
                  responsive: true,
                  displayModeBar: true,
                }}
                useResizeHandler={true}
              />
            </div>
          ) : !Plot && timestamps.length > 0 ? (
            <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
              <Spin tip="加载图表组件..." />
            </div>
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

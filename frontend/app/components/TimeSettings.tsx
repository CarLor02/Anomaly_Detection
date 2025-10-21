import { Typography, Spin, message } from "antd";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { useEffect, useState } from "react";

const { Title } = Typography;

interface TimeSettingsProps {
  selectedFile?: string;
}

export default function TimeSettings({ selectedFile }: TimeSettingsProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [timestamps, setTimestamps] = useState<string[]>([]);
  const [values, setValues] = useState<number[]>([]);
  const [Plot, setPlot] = useState<any>(null);

  // 在客户端动态加载 Plotly
  useEffect(() => {
    import("react-plotly.js").then((module) => {
      setPlot(() => module.default);
    });
  }, []);

  useEffect(() => {
    if (selectedFile) {
      fetchFileData(selectedFile);
    } else {
      // 清空数据
      setTimestamps([]);
      setValues([]);
    }
  }, [selectedFile]);

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

  return (
    <PanelGroup direction="horizontal" style={{ height: "100%" }}>
      <Panel defaultSize={30} minSize={20} maxSize={50}>
        <div style={{ height: "100%", padding: "16px", borderRight: "1px solid #f0f0f0" }}>
          <Title level={5}>检测时间设置</Title>
          <p>时间参数设置区域</p>
          {selectedFile && (
            <div style={{ marginTop: "16px", fontSize: "12px", color: "#666" }}>
              <div>当前文件:</div>
              <div style={{ wordBreak: "break-all" }}>{selectedFile}</div>
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
        <div style={{ height: "100%", width: "100%", display: "flex", flexDirection: "column" }}>
          {loading ? (
            <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center" }}>
              <Spin tip="加载数据中..." />
            </div>
          ) : timestamps.length > 0 && Plot ? (
            <div style={{ flex: 1, width: "100%", height: "100%" }}>
              <Plot
                data={[
                  {
                    x: timestamps,
                    y: values,
                    type: "scatter",
                    mode: "lines",
                    line: { color: "#1890ff" },
                    name: "时序数据",
                  },
                ]}
                layout={{
                  autosize: true,
                  margin: { l: 50, r: 20, t: 20, b: 50 },
                  xaxis: {
                    autorange: true,
                  },
                  yaxis: {
                    autorange: true,
                  },
                }}
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

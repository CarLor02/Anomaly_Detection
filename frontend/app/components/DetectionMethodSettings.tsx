import { Typography } from "antd";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";

const { Title } = Typography;

interface DetectionMethodSettingsProps {
  verticalRevision?: number;
}

export default function DetectionMethodSettings({ verticalRevision }: DetectionMethodSettingsProps) {
  return (
    <PanelGroup direction="horizontal" style={{ height: "100%" }}>
      <Panel defaultSize={30} minSize={20} maxSize={50}>
        <div style={{ height: "100%", padding: "12px", borderRight: "1px solid #f0f0f0", overflowY: "auto", display: "flex", flexDirection: "column" }}>
          <Title level={5} style={{ margin: "0 0 12px 0", fontSize: "14px" }}>检测方法设置</Title>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: "12px" }}>检测方法参数设置区域</p>
          </div>
        </div>
      </Panel>
      <PanelResizeHandle style={{
        width: "2px",
        backgroundColor: "#f0f0f0",
        cursor: "col-resize",
      }} />
      <Panel minSize={50}>
        <div style={{ height: "100%", width: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "16px" }}>
          <p style={{ color: "#999", fontSize: "12px" }}>检测结果图像预览区域</p>
        </div>
      </Panel>
    </PanelGroup>
  );
}

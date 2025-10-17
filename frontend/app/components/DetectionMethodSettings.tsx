import { Typography } from "antd";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";

const { Title } = Typography;

export default function DetectionMethodSettings() {
  return (
    <PanelGroup direction="horizontal" style={{ height: "100%" }}>
      <Panel defaultSize={30} minSize={20} maxSize={50}>
        <div style={{ height: "100%", padding: "16px", borderRight: "1px solid #f0f0f0" }}>
          <Title level={5}>检测方法设置</Title>
          <p>检测方法参数设置区域</p>
        </div>
      </Panel>
      <PanelResizeHandle style={{
        width: "2px",
        backgroundColor: "#f0f0f0",
        cursor: "col-resize",
      }} />
      <Panel minSize={50}>
        <div style={{ height: "100%", padding: "16px" }}>
          <Title level={5}>检测结果预览</Title>
          <p>检测结果图像预览区域</p>
        </div>
      </Panel>
    </PanelGroup>
  );
}

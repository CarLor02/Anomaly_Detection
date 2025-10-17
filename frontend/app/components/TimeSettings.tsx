import { Typography } from "antd";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";

const { Title } = Typography;

export default function TimeSettings() {
  return (
    <PanelGroup direction="horizontal" style={{ height: "100%" }}>
      <Panel defaultSize={30} minSize={20} maxSize={50}>
        <div style={{ height: "100%", padding: "16px", borderRight: "1px solid #f0f0f0" }}>
          <Title level={5}>检测时间设置</Title>
          <p>时间参数设置区域</p>
        </div>
      </Panel>
      <PanelResizeHandle style={{
        width: "2px",
        backgroundColor: "#f0f0f0",
        cursor: "col-resize",
      }} />
      <Panel minSize={50}>
        <div style={{ height: "100%", padding: "16px" }}>
          <Title level={5}>时间预览</Title>
          <p>时间数据图像预览区域</p>
        </div>
      </Panel>
    </PanelGroup>
  );
}

import { Typography } from "antd";

const { Title } = Typography;

export default function DataManagement() {
  return (
    <div style={{ height: "100%", padding: "16px" }}>
      <Title level={4}>数据管理</Title>
      <p>左侧数据管理区域</p>
    </div>
  );
}

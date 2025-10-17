import { useState } from "react";
import type { Route } from "./+types/home";
import { Layout, Menu, Typography } from "antd";
import type { MenuProps } from "antd";
import AnomalyDetection from "../components/AnomalyDetection";

const { Header, Content } = Layout;
const { Title } = Typography;

export function meta({}: Route.MetaArgs) {
  return [
    { title: "时序异常检测" },
    { name: "description", content: "时序异常检测系统" },
  ];
}

export default function Home() {
  const [current, setCurrent] = useState<string>("detection");

  const menuItems: MenuProps["items"] = [
    {
      label: "异常检测",
      key: "detection",
    },
  ];

  const onClick: MenuProps["onClick"] = (e) => {
    setCurrent(e.key);
  };

  return (
    <Layout style={{ height: "100vh" }}>
      <Header style={{ display: "flex", alignItems: "center", background: "#fff" }}>
        <Title level={3} style={{ margin: 0, marginRight: "40px" }}>
          时序异常检测
        </Title>
        <Menu
          onClick={onClick}
          selectedKeys={[current]}
          mode="horizontal"
          items={menuItems}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Content style={{ padding: "12px", display: "flex", flexDirection: "column" }}>
        <div style={{ 
          background: "#fff", 
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden"
        }}>
          <AnomalyDetection />
        </div>
      </Content>
    </Layout>
  );
}

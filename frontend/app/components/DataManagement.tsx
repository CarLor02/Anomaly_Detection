import { Typography, Tree, Spin, message } from "antd";
import { useEffect, useState, useMemo } from "react";
import type { TreeDataNode } from "antd";
import { 
  FolderOutlined, 
  FolderOpenOutlined,
  FileTextOutlined,
  FileExcelOutlined,
  FileDoneOutlined
} from "@ant-design/icons";

const { Title } = Typography;

interface FileTreeNode extends TreeDataNode {
  type?: 'folder' | 'file';
  extension?: string;
  selectable?: boolean;
}

interface DataManagementProps {
  onFileSelect?: (filePath: string) => void;
}

export default function DataManagement({ onFileSelect }: DataManagementProps) {
  const [treeData, setTreeData] = useState<FileTreeNode[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);

  useEffect(() => {
    fetchFileTree();
  }, []);

  const fetchFileTree = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:5555/api/data/files");
      const data = await response.json();

      if (data.success) {
        setTreeData(data.tree);
      } else {
        message.error(data.message || "获取文件列表失败");
      }
    } catch (error) {
      console.error("Error fetching file tree:", error);
      message.error("无法连接到后端服务");
    } finally {
      setLoading(false);
    }
  };

  const onSelect = (selectedKeysValue: React.Key[], info: any) => {
    
    // 如果点击的是文件夹，切换展开状态
    if (info.node.type === 'folder') {
      const key = info.node.key;
      if (expandedKeys.includes(key)) {
        setExpandedKeys(expandedKeys.filter(k => k !== key));
      } else {
        setExpandedKeys([...expandedKeys, key]);
      }
      return;
    }
    
    // 如果是文件，进行选中操作
    setSelectedKeys(selectedKeysValue as string[]);
    
    if (selectedKeysValue.length > 0) {
      const filePath = info.node.key;
      message.success(`已选择文件: ${info.node.title}`);
      
      // 调用回调函数，通知父组件文件被选中
      if (onFileSelect) {
        onFileSelect(filePath);
      }
    } else {
      // 取消选中时，通知父组件清空
      message.info('已取消选择');
      if (onFileSelect) {
        onFileSelect('');
      }
    }
  };

  const onExpand = (expandedKeysValue: React.Key[]) => {
    setExpandedKeys(expandedKeysValue);
  };

  // 自定义标题渲染，为文件夹添加点击展开功能，并禁止换行
  const titleRender = (nodeData: any) => {
    const handleTitleClick = (e: React.MouseEvent) => {
      if (nodeData.type === 'folder') {
        e.stopPropagation();
        const key = nodeData.key;
        if (expandedKeys.includes(key)) {
          setExpandedKeys(expandedKeys.filter(k => k !== key));
        } else {
          setExpandedKeys([...expandedKeys, key]);
        }
      }
    };

    return (
      <span 
        onClick={handleTitleClick} 
        style={{ 
          cursor: 'pointer',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          display: 'inline-block',
          maxWidth: '100%'
        }}
        title={nodeData.title}
      >
        {nodeData.title}
      </span>
    );
  };

  const getFileIcon = (item: FileTreeNode, isExpanded: boolean) => {
    if (item.type === 'folder') {
      return isExpanded ? 
        <FolderOpenOutlined style={{ color: '#faad14' }} /> : 
        <FolderOutlined style={{ color: '#faad14' }} />;
    }
    
    // 根据文件扩展名返回不同图标
    switch (item.extension) {
      case '.csv':
        return <FileExcelOutlined style={{ color: '#52c41a' }} />;
      case '.json':
        return <FileDoneOutlined style={{ color: '#1890ff' }} />;
      default:
        return <FileTextOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  const renderTreeNodes = (data: FileTreeNode[]): FileTreeNode[] => {
    return data.map((item) => {
      const isExpanded = expandedKeys.includes(item.key as React.Key);
      return {
        ...item,
        icon: getFileIcon(item, isExpanded),
        children: item.children ? renderTreeNodes(item.children as FileTreeNode[]) : undefined,
      };
    });
  };

  // 使用 useMemo 缓存渲染的树节点，当 treeData 或 expandedKeys 变化时重新计算
  const renderedTreeData = useMemo(() => {
    return renderTreeNodes(treeData);
  }, [treeData, expandedKeys]);

  return (
    <div style={{ height: "100%", padding: "16px", display: "flex", flexDirection: "column" }}>
      <Title level={4}>数据管理</Title>
      
      {loading ? (
        <div style={{ flex: 1 }}>
          <Spin tip="加载文件列表..." spinning={true}>
            <div style={{ minHeight: "200px" }} />
          </Spin>
        </div>
      ) : (
        <div style={{ flex: 1, overflow: "auto" }}>
          {treeData.length > 0 ? (
            <Tree
              showIcon
              selectedKeys={selectedKeys}
              expandedKeys={expandedKeys}
              onSelect={onSelect}
              onExpand={onExpand}
              treeData={renderedTreeData}
              titleRender={titleRender}
              defaultExpandAll={false}
              style={{
                whiteSpace: 'nowrap'
              }}
            />
          ) : (
            <p style={{ color: "#ffffffff" }}>暂无数据文件</p>
          )}
        </div>
      )}
    </div>
  );
}

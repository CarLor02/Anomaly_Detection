import { useState } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import DataManagement from "./DataManagement";
import TimeSettings from "./TimeSettings";
import DataPreprocessing from "./DataPreprocessing";
import DetectionMethodSettings from "./DetectionMethodSettings";

export default function AnomalyDetection() {
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [verticalRevision, setVerticalRevision] = useState<number>(0);

  const handleVerticalResize = () => {
    setVerticalRevision(prev => prev + 1);
  };

  return (
    <div style={{ height: "100%" }}>
      <PanelGroup direction="horizontal" style={{ height: "100%" }}>
        <Panel defaultSize={20} minSize={10} maxSize={50}>
          <div style={{ 
            height: "100%", 
            backgroundColor: "#fafafa",
            borderRight: "1px solid #d9d9d9"
          }}>
            <DataManagement onFileSelect={setSelectedFile} />
          </div>
        </Panel>
        <PanelResizeHandle style={{
          width: "4px",
          backgroundColor: "#d9d9d9",
          cursor: "col-resize",
          transition: "background-color 0.2s",
        }} />
        <Panel minSize={50}>
          <PanelGroup direction="vertical" style={{ height: "100%" }}>
            <Panel defaultSize={33.33} minSize={20} onResize={handleVerticalResize}>
              <div style={{ height: "100%", width: "100%", borderBottom: "1px solid #f0f0f0" }}>
                <TimeSettings selectedFile={selectedFile} verticalRevision={verticalRevision} />
              </div>
            </Panel>
            <PanelResizeHandle style={{
              height: "2px",
              backgroundColor: "#f0f0f0",
              cursor: "row-resize",
            }} />
            <Panel defaultSize={33.33} minSize={20} onResize={handleVerticalResize}>
              <div style={{ height: "100%", width: "100%", borderBottom: "1px solid #f0f0f0" }}>
                <DataPreprocessing verticalRevision={verticalRevision} />
              </div>
            </Panel>
            <PanelResizeHandle style={{
              height: "2px",
              backgroundColor: "#f0f0f0",
              cursor: "row-resize",
            }} />
            <Panel defaultSize={33.34} minSize={20} onResize={handleVerticalResize}>
              <div style={{ height: "100%", width: "100%" }}>
                <DetectionMethodSettings verticalRevision={verticalRevision} />
              </div>
            </Panel>
          </PanelGroup>
        </Panel>
      </PanelGroup>
    </div>
  );
}

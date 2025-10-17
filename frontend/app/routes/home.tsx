import { useEffect, useState } from "react";
import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Home" },
    { name: "description", content: "Home page" },
  ];
}

export default function Home() {
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    // 请求后端 API
    fetch("http://localhost:5555/api/hello")
      .then((response) => response.json())
      .then((data) => {
        setMessage(data.message);
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
        setMessage("Error connecting to backend");
      });
  }, []);

  return (
    <div style={{ 
      width: "100vw", 
      height: "100vh", 
      display: "flex", 
      justifyContent: "center", 
      alignItems: "center",
      backgroundColor: "white"
    }}>
      <div style={{ textAlign: "center" }}>
        <h1>{message}</h1>
      </div>
    </div>
  );
}

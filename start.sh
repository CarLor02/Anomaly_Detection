#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动前后端服务${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查并停止占用端口的进程
kill_port() {
    local port=$1
    local name=$2
    echo -e "\n${YELLOW}检查端口 ${port} (${name})...${NC}"
    
    # 查找占用端口的进程
    local pid=$(lsof -ti:${port})
    
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}发现端口 ${port} 被进程 ${pid} 占用，正在终止...${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
        echo -e "${GREEN}端口 ${port} 已释放${NC}"
    else
        echo -e "${GREEN}端口 ${port} 可用${NC}"
    fi
}

# 释放前后端端口
kill_port 5555 "后端"
kill_port 3333 "前端"

# 激活虚拟环境并启动后端
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}启动后端服务 (端口 5555)...${NC}"
echo -e "${GREEN}========================================${NC}"

cd backend

# 检查虚拟环境是否存在
if [ ! -d "../venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在，请先创建虚拟环境${NC}"
    exit 1
fi

# 激活虚拟环境并启动后端
source ../venv/bin/activate

# 检查依赖是否已安装
if ! python -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}正在安装后端依赖...${NC}"
    pip install -r requirements.txt
fi

# 后台启动后端
nohup python app.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}后端已启动 (PID: ${BACKEND_PID})${NC}"
echo -e "${GREEN}后端日志: backend.log${NC}"

cd ..

# 启动前端
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}启动前端服务 (端口 3333)...${NC}"
echo -e "${GREEN}========================================${NC}"

cd frontend

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}正在安装前端依赖...${NC}"
    npm install
fi

# 后台启动前端
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}前端已启动 (PID: ${FRONTEND_PID})${NC}"
echo -e "${GREEN}前端日志: frontend.log${NC}"

cd ..

# 等待服务启动
echo -e "\n${YELLOW}等待服务启动...${NC}"
sleep 3

# 检查服务是否正常运行
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}服务状态检查${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查后端
if curl -s http://localhost:5555/api/hello > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务运行正常: http://localhost:5555${NC}"
else
    echo -e "${RED}✗ 后端服务启动失败，请查看 backend.log${NC}"
fi

# 检查前端
if lsof -ti:3333 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 前端服务运行正常: http://localhost:3333${NC}"
else
    echo -e "${RED}✗ 前端服务启动失败，请查看 frontend.log${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}所有服务已启动！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "前端地址: ${YELLOW}http://localhost:3333${NC}"
echo -e "后端地址: ${YELLOW}http://localhost:5555${NC}"
echo -e "\n日志文件:"
echo -e "  后端: ${YELLOW}backend.log${NC}"
echo -e "  前端: ${YELLOW}frontend.log${NC}"
echo -e "\n要停止服务，请运行: ${YELLOW}./stop_all.sh${NC}"
echo -e "${GREEN}========================================${NC}"

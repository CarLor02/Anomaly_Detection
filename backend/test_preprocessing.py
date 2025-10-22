#!/usr/bin/env python3
"""
预处理 API 测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:5555/api/preprocessing"

def test_get_methods():
    """测试获取预处理方法列表"""
    print("=" * 50)
    print("测试: 获取预处理方法列表")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/methods")
    data = response.json()
    
    print(f"状态: {response.status_code}")
    print(f"成功: {data.get('success')}")
    print("\n支持的平滑方法:")
    
    smooth_methods = data.get('data', {}).get('smooth', {})
    for method_name, method_info in smooth_methods.items():
        print(f"\n  {method_name}:")
        print(f"    名称: {method_info['name']}")
        print(f"    描述: {method_info['description']}")
        print(f"    参数: {method_info['params']}")
    print()

def test_smooth_single():
    """测试单个平滑方法"""
    print("=" * 50)
    print("测试: 应用移动平均平滑")
    print("=" * 50)
    
    # 测试数据
    test_data = {
        "timestamps": ["2024-01-01 00:00:00", "2024-01-01 01:00:00", "2024-01-01 02:00:00", 
                      "2024-01-01 03:00:00", "2024-01-01 04:00:00", "2024-01-01 05:00:00"],
        "values": [1.0, 5.0, 2.0, 8.0, 3.0, 6.0],
        "method": "moving_average",
        "window_size": 3
    }
    
    print(f"原始数据: {test_data['values']}")
    
    response = requests.post(f"{BASE_URL}/smooth", json=test_data)
    data = response.json()
    
    print(f"状态: {response.status_code}")
    print(f"成功: {data.get('success')}")
    
    if data.get('success'):
        smoothed_values = data.get('data', {}).get('values', [])
        print(f"平滑后数据: {[round(v, 2) for v in smoothed_values]}")
    else:
        print(f"错误: {data.get('message')}")
    print()

def test_pipeline():
    """测试预处理流程"""
    print("=" * 50)
    print("测试: 应用预处理流程 (移动平均 + 高斯平滑)")
    print("=" * 50)
    
    # 测试数据
    test_data = {
        "timestamps": ["2024-01-01 00:00:00", "2024-01-01 01:00:00", "2024-01-01 02:00:00", 
                      "2024-01-01 03:00:00", "2024-01-01 04:00:00", "2024-01-01 05:00:00",
                      "2024-01-01 06:00:00", "2024-01-01 07:00:00"],
        "values": [1.0, 5.0, 2.0, 8.0, 3.0, 6.0, 4.0, 7.0],
        "methods": [
            {
                "type": "smooth",
                "params": {
                    "method": "moving_average",
                    "window_size": 3
                }
            },
            {
                "type": "smooth",
                "params": {
                    "method": "gaussian",
                    "window_size": 3
                }
            }
        ]
    }
    
    print(f"原始数据: {test_data['values']}")
    print(f"预处理步骤:")
    for i, method in enumerate(test_data['methods'], 1):
        print(f"  {i}. {method['params']['method']} (窗口大小={method['params']['window_size']})")
    
    response = requests.post(f"{BASE_URL}/apply-pipeline", json=test_data)
    data = response.json()
    
    print(f"\n状态: {response.status_code}")
    print(f"成功: {data.get('success')}")
    
    if data.get('success'):
        processed_values = data.get('data', {}).get('values', [])
        print(f"处理后数据: {[round(v, 2) for v in processed_values]}")
    else:
        print(f"错误: {data.get('message')}")
    print()

def test_all_methods():
    """测试所有平滑方法"""
    print("=" * 50)
    print("测试: 所有平滑方法")
    print("=" * 50)
    
    test_values = [1.0, 5.0, 2.0, 8.0, 3.0, 6.0, 4.0, 7.0]
    methods = ['moving_average', 'exponential', 'gaussian']
    
    print(f"原始数据: {test_values}\n")
    
    for method in methods:
        test_data = {
            "timestamps": [f"2024-01-01 {i:02d}:00:00" for i in range(len(test_values))],
            "values": test_values,
            "method": method,
            "window_size": 3
        }
        
        response = requests.post(f"{BASE_URL}/smooth", json=test_data)
        data = response.json()
        
        if data.get('success'):
            smoothed_values = data.get('data', {}).get('values', [])
            print(f"{method:20s}: {[round(v, 2) for v in smoothed_values]}")
        else:
            print(f"{method:20s}: 错误 - {data.get('message')}")
    print()

if __name__ == "__main__":
    try:
        # 运行所有测试
        test_get_methods()
        test_smooth_single()
        test_all_methods()
        test_pipeline()
        
        print("=" * 50)
        print("✅ 所有测试完成!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("❌ 错误: 无法连接到后端服务")
        print("请确保后端服务正在运行: http://localhost:5555")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

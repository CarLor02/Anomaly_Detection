#!/usr/bin/env python3
"""
测试后端API的脚本
用于验证数据清洗功能是否正常工作
"""
import requests
import json

BASE_URL = "http://localhost:5555"

def test_detection():
    """测试检测API"""
    print("=== 测试检测 API ===")
    
    url = f"{BASE_URL}/api/detection/detect"
    payload = {
        "timestamps": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06"],
        "values": [1.0, 2.0, 3.0, 4.0, 5.0, 100.0],
        "method": {
            "type": "3sigma",
            "params": {
                "sigma_threshold": 3.0
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"成功: {result.get('success')}")
        if result.get('success'):
            data = result.get('data', {})
            stats = data.get('stats', {})
            print(f"异常点数: {stats.get('anomaly_count')}")
            print(f"异常索引: {data.get('anomaly_indices')}")
            print(f"数据质量: {stats.get('data_quality')}")
        else:
            print(f"错误消息: {result.get('message')}")
        print("✅ 检测API测试完成\n")
    except Exception as e:
        print(f"❌ 检测API测试失败: {str(e)}\n")

def test_preprocessing():
    """测试预处理API"""
    print("=== 测试预处理 API ===")
    
    url = f"{BASE_URL}/api/preprocessing/apply-pipeline"
    payload = {
        "timestamps": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-06"],
        "values": [1.0, 5.0, 3.0, 7.0, 2.0, 6.0],
        "methods": [
            {
                "type": "smooth",
                "params": {
                    "method": "moving_average",
                    "window_size": 3
                }
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"成功: {result.get('success')}")
        if result.get('success'):
            data = result.get('data', {})
            print(f"原始值: {payload['values']}")
            print(f"处理后: {data.get('values')}")
        else:
            print(f"错误消息: {result.get('message')}")
        print("✅ 预处理API测试完成\n")
    except Exception as e:
        print(f"❌ 预处理API测试失败: {str(e)}\n")

def test_with_invalid_data():
    """测试包含无效数据的情况"""
    print("=== 测试包含NaN的数据 ===")
    
    url = f"{BASE_URL}/api/detection/detect"
    payload = {
        "timestamps": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "values": [1.0, None, 3.0, 4.0],  # None会被转换为NaN
        "method": {
            "type": "3sigma",
            "params": {
                "sigma_threshold": 3.0
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"成功: {result.get('success')}")
        if result.get('success'):
            data = result.get('data', {})
            stats = data.get('stats', {})
            print(f"总数据点: {stats.get('total_points')}")
            print(f"有效数据点: {stats.get('valid_points')}")
            print(f"无效数据点: {stats.get('invalid_points')}")
            print(f"数据质量: {stats.get('data_quality')}")
        else:
            print(f"错误消息: {result.get('message')}")
        print("✅ 无效数据测试完成\n")
    except Exception as e:
        print(f"❌ 无效数据测试失败: {str(e)}\n")

if __name__ == "__main__":
    print("开始测试后端API...\n")
    print("请确保后端服务正在运行 (./start.sh)\n")
    
    test_detection()
    test_preprocessing()
    test_with_invalid_data()
    
    print("所有测试完成！")

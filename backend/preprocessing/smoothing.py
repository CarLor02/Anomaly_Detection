"""
数据平滑预处理方法
支持多种平滑算法：移动平均、指数平滑、高斯平滑
"""

import numpy as np
from typing import List, Dict, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class DataSmoothing:
    """
    数据平滑类
    支持的平滑方法：
    - moving_average: 移动平均
    - exponential: 指数平滑
    - gaussian: 高斯平滑
    """
    
    SUPPORTED_METHODS = ['moving_average', 'exponential', 'gaussian']
    
    @staticmethod
    def apply(values: List[float], method: str = 'moving_average', window_size: int = 5) -> List[float]:
        """
        应用平滑方法
        
        注意：数据验证应在调用此方法前完成（在routes层）
        此方法会自动清洗数据中的NaN和Inf值（使用插值填充）
        
        Args:
            values: 输入数据值列表（应已通过验证）
            method: 平滑方法 ('moving_average', 'exponential', 'gaussian')
            window_size: 窗口大小
            
        Returns:
            平滑后的数据值列表
        """
        if not values or len(values) == 0:
            return []
        
        if window_size < 1:
            return values
        
        if method not in DataSmoothing.SUPPORTED_METHODS:
            raise ValueError(f"不支持的平滑方法: {method}. 支持的方法: {DataSmoothing.SUPPORTED_METHODS}")
        
        # 使用统一的数据清洗模块（数据验证已在routes层完成）
        valid_data, valid_mask, valid_indices = clean_data(values)
        
        # 如果没有有效数据，返回原数据（理论上不应该发生，因为routes层已验证）
        if len(valid_data) == 0:
            return values
        
        # 转换为 numpy 数组
        data = np.array(values, dtype=float)
        
        # 使用线性插值填充无效值
        if len(valid_data) < len(values):
            data[~valid_mask] = np.interp(np.where(~valid_mask)[0], valid_indices, valid_data)
        
        if method == 'moving_average':
            result = DataSmoothing._moving_average(data, window_size)
        elif method == 'exponential':
            result = DataSmoothing._exponential_smoothing(data, window_size)
        elif method == 'gaussian':
            result = DataSmoothing._gaussian_smoothing(data, window_size)
        else:
            result = data
        
        # 再次检查结果中是否有 NaN 或 Inf
        if np.any(np.isnan(result)) or np.any(np.isinf(result)):
            print(f"警告: 平滑后的数据包含 NaN 或 Inf 值，使用原始数据")
            return values
        
        return result.tolist()
    
    @staticmethod
    def _moving_average(data: np.ndarray, window_size: int) -> np.ndarray:
        """
        移动平均平滑
        
        Args:
            data: 输入数据
            window_size: 窗口大小
            
        Returns:
            平滑后的数据
        """
        half_window = window_size // 2
        result = np.zeros_like(data)
        
        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window + 1)
            result[i] = np.mean(data[start:end])
        
        return result
    
    @staticmethod
    def _exponential_smoothing(data: np.ndarray, window_size: int) -> np.ndarray:
        """
        指数加权移动平均平滑
        
        Args:
            data: 输入数据
            window_size: 窗口大小（用于计算 alpha）
            
        Returns:
            平滑后的数据
        """
        alpha = 2.0 / (window_size + 1)
        result = np.zeros_like(data)
        result[0] = data[0]
        
        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
        
        return result
    
    @staticmethod
    def _gaussian_smoothing(data: np.ndarray, window_size: int) -> np.ndarray:
        """
        高斯平滑
        
        Args:
            data: 输入数据
            window_size: 窗口大小
            
        Returns:
            平滑后的数据
        """
        half_window = window_size // 2
        sigma = window_size / 3.0
        result = np.zeros_like(data)
        
        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window + 1)
            
            # 计算高斯权重
            distances = np.arange(start, end) - i
            weights = np.exp(-(distances ** 2) / (2 * sigma ** 2))
            
            # 加权平均
            result[i] = np.sum(data[start:end] * weights) / np.sum(weights)
        
        return result
    
    @staticmethod
    def get_method_info() -> Dict[str, Any]:
        """
        获取所有支持的平滑方法信息
        
        Returns:
            方法信息字典
        """
        return {
            'smooth': {
                'name': '数据平滑',
                'description': '对时间序列数据进行平滑处理，减少噪声',
                'params': {
                    'method': {
                        'type': 'select',
                        'default': 'moving_average',
                        'options': [
                            {'label': '移动平均', 'value': 'moving_average'},
                            {'label': '指数平滑', 'value': 'exponential'},
                            {'label': '高斯平滑', 'value': 'gaussian'}
                        ],
                        'description': '平滑算法'
                    },
                    'window_size': {
                        'type': 'int',
                        'default': 5,
                        'min': 1,
                        'max': 100,
                        'description': '窗口大小'
                    }
                }
            }
        }

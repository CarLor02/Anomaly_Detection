"""
数据平滑预处理方法
支持多种平滑算法：移动平均、指数平滑、高斯平滑
"""

import numpy as np
from typing import List, Dict, Any


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
        
        Args:
            values: 输入数据值列表
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
        
        # 转换为 numpy 数组以提高计算效率
        data = np.array(values, dtype=float)
        
        # 检查并处理 NaN 和 Inf 值
        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
            print(f"警告: 输入数据包含 NaN 或 Inf 值")
            # 将 NaN 和 Inf 替换为相邻有效值的平均值
            mask = np.isnan(data) | np.isinf(data)
            if np.all(mask):
                # 如果全是无效值，返回全零
                return [0.0] * len(values)
            # 使用线性插值填充无效值
            valid_indices = np.where(~mask)[0]
            if len(valid_indices) > 0:
                data[mask] = np.interp(np.where(mask)[0], valid_indices, data[valid_indices])
        
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

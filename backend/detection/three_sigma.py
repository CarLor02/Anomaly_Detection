"""
3-Sigma异常检测方法
基于正态分布假设，超出均值±3倍标准差的数据点被视为异常点
"""
import numpy as np
from typing import List, Dict, Tuple, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class ThreeSigmaDetection:
    """
    3-Sigma 异常检测方法
    
    注意：此类假设输入数据已经过验证（在routes层完成）
    """
    
    @staticmethod
    def detect(values: List[float], sigma_threshold: float = 3.0) -> Tuple[List[bool], Dict[str, Any]]:
        """
        使用 3-Sigma 方法检测异常
        
        注意：数据验证应在调用此方法前完成（在routes层）
        此方法会自动清洗数据中的NaN和Inf值
        
        Args:
            values: 时间序列数据（应已通过验证）
            sigma_threshold: Sigma 阈值（倍数），默认为 3.0
            
        Returns:
            Tuple[List[bool], Dict[str, Any]]: 
                - 异常标记列表（True 表示异常）
                - 统计信息字典
        """
        if not values or len(values) == 0:
            return [], {}
        
        # 数据清洗，移除NaN和Inf（由统一的数据清洗模块处理）
        valid_data, valid_mask, valid_indices = clean_data(values)
        
        # 如果没有有效数据（理论上不应该发生，因为routes层已验证）
        if len(valid_data) == 0:
            return [False] * len(values), {
                'mean': 0.0,
                'std': 0.0,
                'upper_bound': 0.0,
                'lower_bound': 0.0,
                'total_points': len(values),
                'valid_points': 0,
                'invalid_points': len(values),
                'anomaly_count': 0,
                'anomaly_ratio': 0.0
            }
        
        # 计算均值和标准差（仅使用有效数据）
        mean = np.mean(valid_data)
        std = np.std(valid_data)
        
        # 计算上下界
        upper_bound = mean + sigma_threshold * std
        lower_bound = mean - sigma_threshold * std
        
        # 检测异常（仅在有效数据中检测）
        valid_anomalies = (valid_data > upper_bound) | (valid_data < lower_bound)
        
        # 将异常结果映射回原始索引（转换为Python bool以便JSON序列化）
        anomalies = [False] * len(values)
        for i, valid_idx in enumerate(valid_indices):
            anomalies[valid_idx] = bool(valid_anomalies[i])
        
        # 统计信息
        stats = {
            'mean': float(mean),
            'std': float(std),
            'upper_bound': float(upper_bound),
            'lower_bound': float(lower_bound),
            'total_points': len(values),
            'valid_points': len(valid_data),
            'invalid_points': len(values) - len(valid_data),
            'anomaly_count': int(np.sum(valid_anomalies)),
            'anomaly_ratio': float(np.sum(valid_anomalies) / len(valid_data))
        }
        
        return anomalies, stats
    
    @staticmethod
    def get_method_info() -> Dict[str, Any]:
        """
        获取 3-Sigma 方法的配置信息
        
        Returns:
            方法配置字典
        """
        return {
            '3sigma': {
                'name': '3-Sigma 检测',
                'category': '统计型',
                'description': '基于正态分布假设的经典统计方法。计算数据的均值(μ)和标准差(σ)，将偏离均值超过 N×σ 的数据点标记为异常。适用于近似正态分布的数据。',
                'principle': '假设数据服从正态分布，根据3σ原则，99.7%的数据应落在[μ-3σ, μ+3σ]区间内，超出此区间的数据点被视为异常。',
                'params': {
                    'sigma_threshold': {
                        'type': 'float',
                        'default': 3.0,
                        'step': 0.1,
                        'description': 'Sigma 阈值（倍数）',
                        'detail': '设置偏离均值的标准差倍数。3σ对应99.7%置信度，2σ对应95.4%，值越大检测越保守。'
                    }
                }
            }
        }

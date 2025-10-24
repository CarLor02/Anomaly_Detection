"""
IQR (Interquartile Range) 异常检测方法
基于四分位距，识别超出 [Q1 - k*IQR, Q3 + k*IQR] 范围的异常点
"""
import numpy as np
from typing import List, Dict, Tuple, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class IQRDetection:
    """
    IQR 异常检测方法
    
    注意：此类假设输入数据已经过验证（在routes层完成）
    """
    
    @staticmethod
    def detect(values: List[float], iqr_multiplier: float = 1.5) -> Tuple[List[bool], Dict[str, Any]]:
        """
        使用 IQR 方法检测异常
        
        注意：数据验证应在调用此方法前完成（在routes层）
        此方法会自动清洗数据中的NaN和Inf值
        
        Args:
            values: 时间序列数据（应已通过验证）
            iqr_multiplier: IQR 倍数（默认1.5，常用值：1.5为离群值，3.0为极端离群值）
            
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
                'q1': 0.0,
                'q2': 0.0,
                'q3': 0.0,
                'iqr': 0.0,
                'lower_bound': 0.0,
                'upper_bound': 0.0,
                'total_points': len(values),
                'valid_points': 0,
                'invalid_points': len(values),
                'anomaly_count': 0,
                'anomaly_ratio': 0.0
            }
        
        # 计算四分位数（仅使用有效数据）
        q1 = float(np.percentile(valid_data, 25))
        q2 = float(np.percentile(valid_data, 50))  # 中位数
        q3 = float(np.percentile(valid_data, 75))
        
        # 计算四分位距 (IQR)
        iqr = q3 - q1
        
        # 计算上下界
        lower_bound = q1 - iqr_multiplier * iqr
        upper_bound = q3 + iqr_multiplier * iqr
        
        # 检测异常（仅在有效数据中检测）
        valid_anomalies = (valid_data < lower_bound) | (valid_data > upper_bound)
        
        # 将异常结果映射回原始索引（转换为Python bool以便JSON序列化）
        anomalies = [False] * len(values)
        for i, valid_idx in enumerate(valid_indices):
            anomalies[valid_idx] = bool(valid_anomalies[i])
        
        # 统计信息
        stats = {
            'q1': q1,
            'q2': q2,  # 中位数
            'q3': q3,
            'iqr': iqr,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
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
        获取 IQR 方法的配置信息
        
        Returns:
            方法配置字典
        """
        return {
            'iqr': {
                'name': 'IQR 检测',
                'category': '统计型',
                'description': '基于四分位距的稳健统计方法，不受极端值影响。通过计算数据的四分位数来确定异常边界，适用于非正态分布的数据。',
                'principle': '计算第一四分位数(Q1)、第三四分位数(Q3)和四分位距(IQR=Q3-Q1)，将超出[Q1-k×IQR, Q3+k×IQR]范围的点标记为异常。箱线图的经典方法。',
                'params': {
                    'iqr_multiplier': {
                        'type': 'float',
                        'default': 1.5,
                        'min': 0.5,
                        'max': 5.0,
                        'step': 0.1,
                        'description': 'IQR 倍数',
                        'detail': 'IQR的倍数系数。1.5为标准值（识别离群值），3.0识别极端离群值。值越大检测越保守。'
                    }
                }
            }
        }

"""
NormA异常检测方法
基于归一化距离的异常检测算法，通过计算数据点与正常模式的归一化偏差来识别异常
适用于检测偏离正常分布的异常点
"""
import numpy as np
from typing import List, Dict, Tuple, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class NormADetection:
    """
    NormA (Normalized Anomaly) 异常检测方法
    
    注意：此类假设输入数据已经过验证（在routes层完成）
    """
    
    @staticmethod
    def detect(values: List[float], window_size: int = 10, contamination: float = 0.1, sensitivity: float = 1.0) -> Tuple[List[bool], Dict[str, Any]]:
        """
        使用NormA方法检测异常
        
        Args:
            values: 输入的数值数据
            window_size: 滑动窗口大小（用于局部统计）
            contamination: 异常数据比例
            sensitivity: 敏感度系数（越大越敏感）
            
        Returns:
            (异常标记列表, 统计信息字典)
        """
        # 数据清洗
        cleaned_values, valid_mask, valid_indices = clean_data(values)
        
        # 统计信息
        total_points = len(values)
        valid_points = np.sum(valid_mask)
        invalid_points = total_points - valid_points
        
        # 初始化异常标记
        anomalies = [False] * total_points
        
        # 如果有效数据点不足，返回空结果
        if valid_points < window_size:
            stats = {
                'total_points': int(total_points),
                'valid_points': int(valid_points),
                'invalid_points': int(invalid_points),
                'anomaly_count': 0,
                'anomaly_ratio': 0.0
            }
            return anomalies, stats
        
        # 提取有效数据及其索引
        valid_indices = np.where(valid_mask)[0]
        valid_values = cleaned_values[valid_mask]
        n = len(valid_values)
        
        # 计算局部归一化距离
        anomaly_scores = np.zeros(n)
        
        for i in range(n):
            # 确定窗口范围
            start = max(0, i - window_size // 2)
            end = min(n, i + window_size // 2 + 1)
            
            # 提取局部窗口（排除当前点）
            window_indices = list(range(start, i)) + list(range(i + 1, end))
            if len(window_indices) == 0:
                anomaly_scores[i] = 0
                continue
            
            window_data = valid_values[window_indices]
            
            # 计算局部统计量
            local_mean = np.mean(window_data)
            local_std = np.std(window_data)
            local_median = np.median(window_data)
            
            # 计算归一化距离
            if local_std > 0:
                # 标准化偏差
                z_score = abs(valid_values[i] - local_mean) / local_std
                
                # 中位数绝对偏差 (MAD)
                mad = np.median(np.abs(window_data - local_median))
                if mad > 0:
                    mad_score = abs(valid_values[i] - local_median) / mad
                else:
                    mad_score = 0
                
                # 结合多种度量
                anomaly_scores[i] = (z_score + mad_score) / 2 * sensitivity
            else:
                # 如果局部标准差为0，检查点是否与局部均值不同
                if abs(valid_values[i] - local_mean) > 1e-10:
                    anomaly_scores[i] = 10.0 * sensitivity
                else:
                    anomaly_scores[i] = 0
        
        # 确定阈值
        threshold_idx = int((1 - contamination) * len(anomaly_scores))
        threshold = np.sort(anomaly_scores)[threshold_idx] if threshold_idx < len(anomaly_scores) else np.max(anomaly_scores)
        
        # 标记异常
        anomaly_count = 0
        for i, score in enumerate(anomaly_scores):
            if score > threshold:
                original_idx = valid_indices[i]
                anomalies[original_idx] = True
                anomaly_count += 1
        
        # 统计信息
        stats = {
            'total_points': int(total_points),
            'valid_points': int(valid_points),
            'invalid_points': int(invalid_points),
            'anomaly_count': int(anomaly_count),
            'anomaly_ratio': float(anomaly_count / total_points if total_points > 0 else 0),
            'window_size': int(window_size),
            'threshold': float(threshold),
            'mean_score': float(np.mean(anomaly_scores)),
            'max_score': float(np.max(anomaly_scores)),
            'min_score': float(np.min(anomaly_scores)),
            'sensitivity': float(sensitivity)
        }
        
        return anomalies, stats
    
    @staticmethod
    def get_method_info() -> Dict[str, Any]:
        """
        获取 NormA 方法的配置信息
        
        Returns:
            方法配置字典
        """
        return {
            'norma': {
                'name': 'NormA 检测',
                'category': '距离型',
                'description': '基于归一化距离的异常检测方法。通过计算数据点与其局部邻域的归一化偏差来识别异常。结合Z-Score和MAD等多种统计量，适用于检测偏离局部正常模式的异常点。',
                'principle': '对每个数据点，在其局部窗口内计算多种归一化距离度量（Z-Score和中位数绝对偏差MAD）。这些度量反映了数据点与局部正常模式的偏离程度。异常分数最高的contamination比例的点被标记为异常。sensitivity参数控制检测敏感度。',
                'params': {
                    'window_size': {
                        'type': 'int',
                        'default': 10,
                        'step': 1,
                        'description': '窗口大小',
                        'detail': '用于计算局部统计量的窗口大小。较小的窗口对局部异常更敏感，较大的窗口考虑更广的上下文。建议根据数据的局部变化特征选择。'
                    },
                    'contamination': {
                        'type': 'float',
                        'default': 0.1,
                        'step': 0.01,
                        'description': '异常数据比例',
                        'detail': '预期的异常数据占总数据的比例。归一化距离最大的contamination比例的点被标记为异常。'
                    },
                    'sensitivity': {
                        'type': 'float',
                        'default': 1.0,
                        'step': 0.1,
                        'description': '敏感度',
                        'detail': '控制异常检测的敏感程度。大于1会增加敏感度（检测出更多异常），小于1会降低敏感度（更保守）。建议从1.0开始调整。'
                    }
                }
            }
        }

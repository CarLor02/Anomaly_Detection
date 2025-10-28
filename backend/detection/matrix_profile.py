"""
Matrix Profile异常检测方法
基于时间序列的Matrix Profile算法，通过计算子序列之间的距离来识别异常模式
适用于检测时间序列中的异常子序列和不匹配模式
"""
import numpy as np
from typing import List, Dict, Tuple, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class MatrixProfileDetection:
    """
    Matrix Profile 异常检测方法
    
    注意：此类假设输入数据已经过验证（在routes层完成）
    """
    
    @staticmethod
    def detect(values: List[float], window_size: int = 10, contamination: float = 0.1) -> Tuple[List[bool], Dict[str, Any]]:
        """
        使用Matrix Profile方法检测异常
        
        Args:
            values: 输入的时间序列数据
            window_size: 滑动窗口大小（子序列长度）
            contamination: 异常数据比例
            
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
        if valid_points < window_size * 2:
            stats = {
                'total_points': int(total_points),
                'valid_points': int(valid_points),
                'invalid_points': int(invalid_points),
                'anomaly_count': 0,
                'anomaly_ratio': 0.0
            }
            return anomalies, stats
        
        # 提取有效数据
        valid_values = cleaned_values[valid_mask]
        
        # 计算Matrix Profile
        n = len(valid_values)
        m = window_size
        
        # 初始化Matrix Profile数组
        matrix_profile = np.full(n - m + 1, np.inf)
        
        # 计算每个子序列到其最近邻的距离
        for i in range(n - m + 1):
            query = valid_values[i:i + m]
            min_dist = np.inf
            
            # 计算与其他子序列的距离（排除自身和邻近窗口）
            for j in range(n - m + 1):
                # 排除自身和重叠部分
                if abs(i - j) < m // 4:
                    continue
                
                candidate = valid_values[j:j + m]
                # 计算欧氏距离
                dist = np.sqrt(np.sum((query - candidate) ** 2))
                
                if dist < min_dist:
                    min_dist = dist
            
            matrix_profile[i] = min_dist
        
        # 标准化Matrix Profile
        mp_mean = np.mean(matrix_profile)
        mp_std = np.std(matrix_profile)
        if mp_std > 0:
            normalized_mp = (matrix_profile - mp_mean) / mp_std
        else:
            normalized_mp = np.zeros_like(matrix_profile)
        
        # 确定异常阈值
        threshold_idx = int((1 - contamination) * len(normalized_mp))
        threshold = np.sort(normalized_mp)[threshold_idx] if threshold_idx < len(normalized_mp) else np.max(normalized_mp)
        
        # 标记异常
        valid_indices = np.where(valid_mask)[0]
        anomaly_count = 0
        
        for i, mp_value in enumerate(normalized_mp):
            if mp_value > threshold:
                # 将整个窗口标记为异常
                start_idx = valid_indices[i] if i < len(valid_indices) else valid_indices[-1]
                end_idx = min(start_idx + m, total_points)
                for idx in range(start_idx, end_idx):
                    if not anomalies[idx]:
                        anomalies[idx] = True
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
            'mean_mp_distance': float(mp_mean),
            'std_mp_distance': float(mp_std),
            'max_mp_distance': float(np.max(matrix_profile))
        }
        
        return anomalies, stats
    
    @staticmethod
    def get_method_info() -> Dict[str, Any]:
        """
        获取 Matrix Profile 方法的配置信息
        
        Returns:
            方法配置字典
        """
        return {
            'matrix_profile': {
                'name': 'Matrix Profile 检测',
                'category': '距离型',
                'description': '基于时间序列相似性的异常检测方法。通过计算每个子序列与其最近邻的距离来识别异常模式。适用于检测时间序列中的不匹配模式和异常子序列。',
                'principle': '计算时间序列的Matrix Profile，即每个子序列到其最近邻（非重叠）子序列的距离。距离较大的子序列表示在整个时间序列中较为独特，可能是异常。距离最大的contamination比例的子序列被标记为异常。',
                'params': {
                    'window_size': {
                        'type': 'int',
                        'default': 10,
                        'step': 1,
                        'description': '窗口大小',
                        'detail': '子序列的长度。应该选择能够捕获异常模式特征的长度。窗口太小可能无法捕获完整模式，太大会降低灵敏度。建议从数据周期性的1/4到1/2开始尝试。'
                    },
                    'contamination': {
                        'type': 'float',
                        'default': 0.1,
                        'step': 0.01,
                        'description': '异常数据比例',
                        'detail': '预期的异常数据占总数据的比例。Matrix Profile距离最大的contamination比例的子序列被标记为异常。'
                    }
                }
            }
        }

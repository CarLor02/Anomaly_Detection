"""
KNN异常检测方法
基于K近邻算法，通过计算每个点到其K个最近邻的平均距离来识别异常点
距离较大的点被视为异常点
"""
import numpy as np
from typing import List, Dict, Tuple, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class KNNDetection:
    """
    KNN 异常检测方法
    
    注意：此类假设输入数据已经过验证（在routes层完成）
    """
    
    @staticmethod
    def detect(values: List[float], n_neighbors: int = 5, contamination: float = 0.1) -> Tuple[List[bool], Dict[str, Any]]:
        """
        使用 KNN 方法检测异常
        
        注意：数据验证应在调用此方法前完成（在routes层）
        此方法会自动清洗数据中的NaN和Inf值
        
        Args:
            values: 时间序列数据（应已通过验证）
            n_neighbors: K近邻的数量，默认为 5
            contamination: 异常数据比例阈值（0-0.5），默认为 0.1
            
        Returns:
            Tuple[List[bool], Dict[str, Any]]: 
                - 异常标记列表（True 表示异常）
                - 统计信息字典
        """
        if not values or len(values) == 0:
            return [], {}
        
        # 数据清洗，移除NaN和Inf（由统一的数据清洗模块处理）
        valid_data, valid_mask, valid_indices = clean_data(values)
        
        # 如果没有有效数据
        if len(valid_data) == 0:
            return [False] * len(values), {
                'total_points': len(values),
                'valid_points': 0,
                'invalid_points': len(values),
                'anomaly_count': 0,
                'anomaly_ratio': 0.0,
                'n_neighbors': n_neighbors,
                'contamination': contamination,
                'threshold_distance': 0.0
            }
        
        # 如果有效数据点数不足 K+1，调整 K 值
        actual_k = min(n_neighbors, len(valid_data) - 1)
        if actual_k < 1:
            # 数据点太少，无法进行KNN检测
            return [False] * len(values), {
                'total_points': len(values),
                'valid_points': len(valid_data),
                'invalid_points': len(values) - len(valid_data),
                'anomaly_count': 0,
                'anomaly_ratio': 0.0,
                'n_neighbors': n_neighbors,
                'contamination': contamination,
                'threshold_distance': 0.0,
                'warning': '数据点太少，无法进行KNN检测'
            }
        
        # 将1维数据转换为2维（索引作为特征）
        # 对于时间序列，我们使用 (index, value) 作为特征
        X = np.column_stack([np.arange(len(valid_data)), valid_data])
        
        # 标准化数据
        X_normalized = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-10)
        
        # 计算每个点到其K个最近邻的平均距离
        distances = []
        for i in range(len(X_normalized)):
            # 计算当前点到所有其他点的欧氏距离
            point_distances = np.sqrt(np.sum((X_normalized - X_normalized[i])**2, axis=1))
            # 排序并获取最近的K个邻居（排除自己）
            k_nearest = np.sort(point_distances)[1:actual_k+1]
            # 计算平均距离
            avg_distance = np.mean(k_nearest)
            distances.append(avg_distance)
        
        distances = np.array(distances)
        
        # 根据contamination参数确定阈值
        # 距离最大的 contamination 比例的点被标记为异常
        threshold_idx = int(len(distances) * (1 - contamination))
        threshold_distance = np.sort(distances)[threshold_idx] if threshold_idx < len(distances) else distances.max()
        
        # 检测异常
        valid_anomalies = distances > threshold_distance
        
        # 将结果映射回原始数据
        anomalies = [False] * len(values)
        for i, idx in enumerate(valid_indices):
            anomalies[idx] = bool(valid_anomalies[i])
        
        # 统计信息（包含前端需要的标准字段）
        stats = {
            # 标准字段（前端必需）
            'total_points': len(values),
            'valid_points': len(valid_data),
            'invalid_points': len(values) - len(valid_data),
            'anomaly_count': int(np.sum(valid_anomalies)),
            'anomaly_ratio': float(np.sum(valid_anomalies) / len(valid_data)) if len(valid_data) > 0 else 0.0,
            # KNN 特定字段
            'n_neighbors': actual_k,
            'contamination': contamination,
            'threshold_distance': float(threshold_distance),
            'mean_distance': float(np.mean(distances)),
            'max_distance': float(np.max(distances)),
            'min_distance': float(np.min(distances))
        }
        
        return anomalies, stats
    
    @staticmethod
    def get_method_info() -> Dict[str, Any]:
        """
        获取 KNN 方法的配置信息
        
        Returns:
            方法配置字典
        """
        return {
            'knn': {
                'name': 'KNN 检测',
                'description': '基于K近邻的局部异常检测方法。通过计算每个点到其K个最近邻的平均距离来度量异常性，距离大的点被视为异常。',
                'principle': '对每个数据点，找到其K个最近邻，计算到这些邻居的平均距离。距离最大的contamination比例的点被标记为异常。适合检测局部稀疏区域的异常点。',
                'params': {
                    'n_neighbors': {
                        'type': 'int',
                        'default': 5,
                        'min': 1,
                        'max': 50,
                        'step': 1,
                        'description': 'K近邻数量',
                        'detail': '用于计算距离的邻居数量。值越大算法越稳定但计算量越大。小数据集建议5-10，大数据集建议20-50。'
                    },
                    'contamination': {
                        'type': 'float',
                        'default': 0.1,
                        'min': 0.01,
                        'max': 0.5,
                        'step': 0.01,
                        'description': '异常数据比例',
                        'detail': '预期的异常点占总数据的比例。0.1表示预期10%的数据是异常。该值决定异常判定的阈值。'
                    }
                }
            }
        }

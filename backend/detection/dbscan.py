"""
DBSCAN异常检测方法
基于密度的聚类算法，将低密度区域的点识别为异常
适用于检测数据中孤立的异常点
"""
import numpy as np
from typing import List, Dict, Tuple, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class DBSCANDetection:
    """
    DBSCAN 异常检测方法
    
    注意：此类假设输入数据已经过验证（在routes层完成）
    """
    
    @staticmethod
    def detect(values: List[float], eps: float = 0.5, min_samples: int = 5) -> Tuple[List[bool], Dict[str, Any]]:
        """
        使用DBSCAN方法检测异常
        
        Args:
            values: 输入的数值数据
            eps: 邻域半径
            min_samples: 核心点的最小邻居数
            
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
        if valid_points < min_samples:
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
        valid_values = cleaned_values[valid_mask].reshape(-1, 1)
        
        # 标准化数据以便设置合适的eps
        mean_val = np.mean(valid_values)
        std_val = np.std(valid_values)
        if std_val > 0:
            normalized_values = (valid_values - mean_val) / std_val
        else:
            normalized_values = valid_values
        
        # 调整eps到标准化空间
        adjusted_eps = eps
        
        # DBSCAN核心算法
        n = len(normalized_values)
        labels = np.full(n, -1)  # -1表示噪声点（异常）
        cluster_id = 0
        visited = np.zeros(n, dtype=bool)
        
        def get_neighbors(point_idx):
            """获取点的邻居"""
            distances = np.abs(normalized_values - normalized_values[point_idx]).flatten()
            return np.where(distances <= adjusted_eps)[0]
        
        def expand_cluster(point_idx, neighbors, cluster_id):
            """扩展聚类"""
            labels[point_idx] = cluster_id
            i = 0
            while i < len(neighbors):
                neighbor_idx = neighbors[i]
                
                if not visited[neighbor_idx]:
                    visited[neighbor_idx] = True
                    neighbor_neighbors = get_neighbors(neighbor_idx)
                    
                    if len(neighbor_neighbors) >= min_samples:
                        neighbors = np.concatenate([neighbors, neighbor_neighbors])
                
                if labels[neighbor_idx] == -1:
                    labels[neighbor_idx] = cluster_id
                
                i += 1
        
        # 执行DBSCAN
        for i in range(n):
            if visited[i]:
                continue
            
            visited[i] = True
            neighbors = get_neighbors(i)
            
            if len(neighbors) >= min_samples:
                expand_cluster(i, neighbors, cluster_id)
                cluster_id += 1
        
        # 标记异常（噪声点）
        anomaly_count = 0
        for i, label in enumerate(labels):
            if label == -1:
                original_idx = valid_indices[i]
                anomalies[original_idx] = True
                anomaly_count += 1
        
        # 统计聚类信息
        unique_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_points = np.sum(labels == -1)
        
        # 统计信息
        stats = {
            'total_points': int(total_points),
            'valid_points': int(valid_points),
            'invalid_points': int(invalid_points),
            'anomaly_count': int(anomaly_count),
            'anomaly_ratio': float(anomaly_count / total_points if total_points > 0 else 0),
            'n_clusters': int(unique_clusters),
            'noise_points': int(noise_points),
            'eps': float(eps),
            'min_samples': int(min_samples)
        }
        
        return anomalies, stats
    
    @staticmethod
    def get_method_info() -> Dict[str, Any]:
        """
        获取 DBSCAN 方法的配置信息
        
        Returns:
            方法配置字典
        """
        return {
            'dbscan': {
                'name': 'DBSCAN 检测',
                'category': '距离型',
                'description': '基于密度的空间聚类算法。将密度较低区域的点识别为噪声（异常），适用于检测孤立的离群点。',
                'principle': '根据数据点的密度进行聚类。核心思想是：高密度区域形成聚类，低密度区域的点（无法达到min_samples个邻居的点）被标记为噪声点，即异常。eps参数定义邻域半径，min_samples定义核心点的最小邻居数。',
                'params': {
                    'eps': {
                        'type': 'float',
                        'default': 0.5,
                        'min': 0.1,
                        'max': 5.0,
                        'step': 0.1,
                        'description': '邻域半径',
                        'detail': '定义点的邻域范围（以标准差为单位）。较小的eps会产生更多的噪声点（异常），较大的eps会将更多点聚为一类。建议从0.5开始，根据数据分布调整。'
                    },
                    'min_samples': {
                        'type': 'int',
                        'default': 5,
                        'min': 2,
                        'max': 20,
                        'step': 1,
                        'description': '最小样本数',
                        'detail': '成为核心点所需的最小邻居数（包括自己）。较大的值会产生更多噪声点（异常），较小的值会形成更密集的聚类。建议设置为数据集大小的1-2%。'
                    }
                }
            }
        }

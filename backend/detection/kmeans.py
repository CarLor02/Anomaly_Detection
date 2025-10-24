"""
K-Means异常检测方法
基于K-Means聚类算法，将数据点到最近簇中心的距离作为异常分数
距离较远的点被视为异常点
"""
import numpy as np
from typing import List, Dict, Tuple, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class KMeansDetection:
    """
    K-Means 异常检测方法
    
    注意：此类假设输入数据已经过验证（在routes层完成）
    """
    
    @staticmethod
    def detect(values: List[float], n_clusters: int = 3, contamination: float = 0.1, max_iter: int = 100) -> Tuple[List[bool], Dict[str, Any]]:
        """
        使用 K-Means 方法检测异常
        
        注意：数据验证应在调用此方法前完成（在routes层）
        此方法会自动清洗数据中的NaN和Inf值
        
        Args:
            values: 时间序列数据（应已通过验证）
            n_clusters: 聚类数量，默认为 3
            contamination: 异常数据比例阈值（0-0.5），默认为 0.1
            max_iter: 最大迭代次数，默认为 100
            
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
                'n_clusters': n_clusters,
                'contamination': contamination,
                'threshold_distance': 0.0
            }
        
        # 如果有效数据点数少于聚类数，调整聚类数
        actual_k = min(n_clusters, len(valid_data))
        if actual_k < 1:
            # 数据点太少
            return [False] * len(values), {
                'total_points': len(values),
                'valid_points': len(valid_data),
                'invalid_points': len(values) - len(valid_data),
                'anomaly_count': 0,
                'anomaly_ratio': 0.0,
                'n_clusters': n_clusters,
                'contamination': contamination,
                'threshold_distance': 0.0,
                'warning': '数据点太少，无法进行聚类'
            }
        
        # 将1维数据转换为2维（索引作为特征）
        X = np.column_stack([np.arange(len(valid_data)), valid_data])
        
        # 标准化数据
        X_normalized = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-10)
        
        # K-Means 聚类
        # 初始化聚类中心（使用K-Means++策略）
        n_points = len(X_normalized)
        centers = [X_normalized[np.random.randint(0, n_points)]]
        
        for _ in range(actual_k - 1):
            # 计算每个点到最近中心的距离
            distances = np.array([min([np.sum((x - c)**2) for c in centers]) for x in X_normalized])
            # 按距离的平方作为概率选择下一个中心
            probabilities = distances / distances.sum()
            cumulative_probs = np.cumsum(probabilities)
            r = np.random.random()
            for idx, prob in enumerate(cumulative_probs):
                if r < prob:
                    centers.append(X_normalized[idx])
                    break
        
        centers = np.array(centers)
        
        # 迭代优化聚类中心
        for iteration in range(max_iter):
            # 分配每个点到最近的聚类中心
            labels = np.zeros(n_points, dtype=int)
            for i, point in enumerate(X_normalized):
                distances_to_centers = np.sqrt(np.sum((centers - point)**2, axis=1))
                labels[i] = np.argmin(distances_to_centers)
            
            # 更新聚类中心
            new_centers = np.zeros_like(centers)
            for k in range(actual_k):
                cluster_points = X_normalized[labels == k]
                if len(cluster_points) > 0:
                    new_centers[k] = cluster_points.mean(axis=0)
                else:
                    # 如果某个聚类没有点，保持原中心
                    new_centers[k] = centers[k]
            
            # 检查收敛
            if np.allclose(centers, new_centers, rtol=1e-6):
                break
            
            centers = new_centers
        
        # 计算每个点到最近聚类中心的距离
        distances_to_cluster = np.zeros(n_points)
        for i, point in enumerate(X_normalized):
            distances_to_centers = np.sqrt(np.sum((centers - point)**2, axis=1))
            distances_to_cluster[i] = np.min(distances_to_centers)
        
        # 根据contamination参数确定阈值
        # 距离最大的 contamination 比例的点被标记为异常
        threshold_idx = int(len(distances_to_cluster) * (1 - contamination))
        threshold_distance = np.sort(distances_to_cluster)[threshold_idx] if threshold_idx < len(distances_to_cluster) else distances_to_cluster.max()
        
        # 检测异常
        valid_anomalies = distances_to_cluster > threshold_distance
        
        # 将结果映射回原始数据
        anomalies = [False] * len(values)
        for i, idx in enumerate(valid_indices):
            anomalies[idx] = bool(valid_anomalies[i])
        
        # 统计每个聚类的大小
        cluster_sizes = [np.sum(labels == k) for k in range(actual_k)]
        
        # 统计信息（包含前端需要的标准字段）
        stats = {
            # 标准字段（前端必需）
            'total_points': len(values),
            'valid_points': len(valid_data),
            'invalid_points': len(values) - len(valid_data),
            'anomaly_count': int(np.sum(valid_anomalies)),
            'anomaly_ratio': float(np.sum(valid_anomalies) / len(valid_data)) if len(valid_data) > 0 else 0.0,
            # K-Means 特定字段
            'n_clusters': actual_k,
            'contamination': contamination,
            'iterations': iteration + 1,
            'threshold_distance': float(threshold_distance),
            'mean_distance': float(np.mean(distances_to_cluster)),
            'max_distance': float(np.max(distances_to_cluster)),
            'min_distance': float(np.min(distances_to_cluster)),
            'cluster_sizes': [int(size) for size in cluster_sizes]
        }
        
        return anomalies, stats
    
    @staticmethod
    def get_method_info() -> Dict[str, Any]:
        """
        获取 K-Means 方法的配置信息
        
        Returns:
            方法配置字典
        """
        return {
            'kmeans': {
                'name': 'K-Means 检测',
                'description': '基于聚类的异常检测方法。先将数据聚为K个簇，然后识别距离簇中心较远的点为异常。适用于数据呈现明显聚类结构的场景。',
                'principle': '使用K-Means算法将数据分为K个簇，计算每个点到最近簇中心的距离。距离最大的contamination比例的点被标记为异常，表示它们偏离正常模式。',
                'params': {
                    'n_clusters': {
                        'type': 'int',
                        'default': 3,
                        'min': 2,
                        'max': 10,
                        'step': 1,
                        'description': '聚类数量',
                        'detail': '将数据分为几个簇。建议根据数据特征选择：先尝试2-5个，观察效果后调整。聚类数过多可能导致过拟合。'
                    },
                    'contamination': {
                        'type': 'float',
                        'default': 0.1,
                        'min': 0.01,
                        'max': 0.5,
                        'step': 0.01,
                        'description': '异常数据比例',
                        'detail': '预期的异常点占总数据的比例。距离簇中心最远的contamination比例的点被标记为异常。'
                    },
                    'max_iter': {
                        'type': 'int',
                        'default': 100,
                        'min': 10,
                        'max': 500,
                        'step': 10,
                        'description': '最大迭代次数',
                        'detail': 'K-Means算法的最大迭代次数。通常100次足够收敛，数据量大时可适当增加。'
                    }
                }
            }
        }

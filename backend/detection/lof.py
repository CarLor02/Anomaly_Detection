"""
LOF异常检测方法
局部离群因子（Local Outlier Factor）算法
通过计算局部密度偏差来识别异常点，适用于发现局部密度明显低于邻域的异常点
"""
import numpy as np
from typing import List, Dict, Tuple, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_cleaner import clean_data


class LOFDetection:
    """
    LOF 异常检测方法
    
    注意：此类假设输入数据已经过验证（在routes层完成）
    """
    
    @staticmethod
    def detect(values: List[float], n_neighbors: int = 20, contamination: float = 0.1) -> Tuple[List[bool], Dict[str, Any]]:
        """
        使用 LOF 方法检测异常
        
        注意：数据验证应在调用此方法前完成（在routes层）
        此方法会自动清洗数据中的NaN和Inf值
        
        Args:
            values: 时间序列数据（应已通过验证）
            n_neighbors: 用于计算局部密度的邻居数量，默认为 20
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
                'threshold_lof': 0.0
            }
        
        # 如果有效数据点数不足 K+1，调整 K 值
        actual_k = min(n_neighbors, len(valid_data) - 1)
        if actual_k < 1:
            # 数据点太少，无法进行LOF检测
            return [False] * len(values), {
                'total_points': len(values),
                'valid_points': len(valid_data),
                'invalid_points': len(values) - len(valid_data),
                'anomaly_count': 0,
                'anomaly_ratio': 0.0,
                'n_neighbors': n_neighbors,
                'contamination': contamination,
                'threshold_lof': 0.0,
                'warning': '数据点太少，无法进行LOF检测'
            }
        
        # 将1维数据转换为2维（索引作为特征）
        X = np.column_stack([np.arange(len(valid_data)), valid_data])
        
        # 标准化数据
        X_normalized = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-10)
        
        # 计算所有点之间的距离矩阵
        n_points = len(X_normalized)
        distances_matrix = np.zeros((n_points, n_points))
        for i in range(n_points):
            for j in range(n_points):
                if i != j:
                    distances_matrix[i, j] = np.sqrt(np.sum((X_normalized[i] - X_normalized[j])**2))
        
        # 计算每个点的LOF值
        lof_scores = []
        for i in range(n_points):
            # 获取K近邻的索引
            distances_to_i = distances_matrix[i].copy()
            k_nearest_indices = np.argpartition(distances_to_i, actual_k)[:actual_k]
            
            # 计算k-距离（到第k个最近邻的距离）
            k_distance_i = distances_to_i[k_nearest_indices].max()
            
            # 计算可达距离密度（LRD）
            reachability_distances = []
            for j in k_nearest_indices:
                distances_to_j = distances_matrix[j].copy()
                k_distance_j = distances_to_j[np.argpartition(distances_to_j, actual_k)[:actual_k]].max()
                reach_dist = max(distances_matrix[i, j], k_distance_j)
                reachability_distances.append(reach_dist)
            
            lrd_i = 1.0 / (np.mean(reachability_distances) + 1e-10)
            
            # 计算邻居的LRD
            neighbor_lrds = []
            for j in k_nearest_indices:
                distances_to_j = distances_matrix[j].copy()
                k_nearest_j = np.argpartition(distances_to_j, actual_k)[:actual_k]
                
                reach_dists_j = []
                for m in k_nearest_j:
                    distances_to_m = distances_matrix[m].copy()
                    k_distance_m = distances_to_m[np.argpartition(distances_to_m, actual_k)[:actual_k]].max()
                    reach_dist_j = max(distances_matrix[j, m], k_distance_m)
                    reach_dists_j.append(reach_dist_j)
                
                lrd_j = 1.0 / (np.mean(reach_dists_j) + 1e-10)
                neighbor_lrds.append(lrd_j)
            
            # 计算LOF值
            lof = np.mean(neighbor_lrds) / (lrd_i + 1e-10)
            lof_scores.append(lof)
        
        lof_scores = np.array(lof_scores)
        
        # 根据contamination参数确定阈值
        # LOF值最大的 contamination 比例的点被标记为异常
        threshold_idx = int(len(lof_scores) * (1 - contamination))
        threshold_lof = np.sort(lof_scores)[threshold_idx] if threshold_idx < len(lof_scores) else lof_scores.max()
        
        # 检测异常（LOF > 1 表示比邻域密度低，值越大越异常）
        valid_anomalies = lof_scores > threshold_lof
        
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
            # LOF 特定字段
            'n_neighbors': actual_k,
            'contamination': contamination,
            'threshold_lof': float(threshold_lof),
            'mean_lof': float(np.mean(lof_scores)),
            'max_lof': float(np.max(lof_scores)),
            'min_lof': float(np.min(lof_scores))
        }
        
        return anomalies, stats
    
    @staticmethod
    def get_method_info() -> Dict[str, Any]:
        """
        获取 LOF 方法的配置信息
        
        Returns:
            方法配置字典
        """
        return {
            'lof': {
                'name': 'LOF 检测',
                'category': '距离型',
                'description': '局部离群因子算法，通过比较点与邻域的密度来识别异常。能够识别不同密度区域中的局部异常，是最经典的密度异常检测方法之一。',
                'principle': '计算每个点的局部可达密度(LRD)，再计算局部离群因子(LOF)，即该点LRD与其邻居LRD的比值。LOF>1表示该点比邻域稀疏（异常），值越大越异常。',
                'params': {
                    'n_neighbors': {
                        'type': 'int',
                        'default': 20,
                        'min': 5,
                        'max': 50,
                        'step': 1,
                        'description': '邻居数量',
                        'detail': '用于计算局部密度的邻居数量。建议设置较大值（20-30）以获得稳定结果。值太小会导致结果不稳定。'
                    },
                    'contamination': {
                        'type': 'float',
                        'default': 0.1,
                        'min': 0.01,
                        'max': 0.5,
                        'step': 0.01,
                        'description': '异常数据比例',
                        'detail': '预期的异常点占总数据的比例。用于确定LOF阈值，LOF最大的contamination比例的点被标记为异常。'
                    }
                }
            }
        }

"""
数据清洗工具模块
提供统一的数据验证和清洗功能，供预处理和检测方法使用
"""
import numpy as np
from typing import Tuple, List


def clean_data(values: List[float]) -> Tuple[np.ndarray, np.ndarray, List[int]]:
    """
    清洗数据，移除NaN和Inf值
    
    Args:
        values: 原始数值列表
        
    Returns:
        Tuple包含:
        - valid_data: 清洗后的有效数据 (numpy数组)
        - valid_mask: 有效数据的布尔掩码 (numpy数组)
        - valid_indices: 有效数据的原始索引列表
    """
    # 尝试转换为float数组，处理可能的字符串等类型
    try:
        data = np.array(values, dtype=float)
    except (ValueError, TypeError):
        # 如果直接转换失败，逐个元素转换
        converted = []
        for v in values:
            try:
                converted.append(float(v))
            except (ValueError, TypeError):
                converted.append(np.nan)
        data = np.array(converted, dtype=float)
    
    valid_mask = np.isfinite(data)
    valid_data = data[valid_mask]
    valid_indices = np.where(valid_mask)[0].tolist()
    
    return valid_data, valid_mask, valid_indices


def validate_data(values: List[float], min_valid_points: int = 3) -> Tuple[bool, str]:
    """
    验证数据是否满足基本要求
    
    Args:
        values: 数值列表
        min_valid_points: 最少有效数据点数量（默认3个）
        
    Returns:
        Tuple包含:
        - is_valid: 数据是否有效
        - message: 验证失败时的错误信息
    """
    if not values or len(values) == 0:
        return False, "数据为空"
    
    # 尝试转换为float数组，处理可能的字符串等类型
    try:
        data = np.array(values, dtype=float)
    except (ValueError, TypeError):
        # 如果直接转换失败，逐个元素转换
        converted = []
        for v in values:
            try:
                converted.append(float(v))
            except (ValueError, TypeError):
                converted.append(np.nan)
        data = np.array(converted, dtype=float)
    
    valid_mask = np.isfinite(data)
    valid_count = np.sum(valid_mask)
    
    if valid_count == 0:
        return False, "所有数据点都是无效值（NaN或Inf）"
    
    if valid_count < min_valid_points:
        return False, f"有效数据点不足（需要至少{min_valid_points}个，实际{valid_count}个）"
    
    invalid_count = len(values) - valid_count
    if invalid_count > 0:
        invalid_ratio = invalid_count / len(values)
        if invalid_ratio > 0.5:
            return False, f"无效数据点过多（{invalid_count}/{len(values)} = {invalid_ratio*100:.1f}%）"
    
    return True, ""


def get_data_quality_info(values: List[float]) -> dict:
    """
    获取数据质量信息
    
    Args:
        values: 数值列表
        
    Returns:
        包含数据质量统计的字典
    """
    if not values:
        return {
            'total_points': 0,
            'valid_points': 0,
            'invalid_points': 0,
            'nan_count': 0,
            'inf_count': 0,
            'valid_ratio': 0.0
        }
    
    # 尝试转换为float数组，处理可能的字符串等类型
    try:
        data = np.array(values, dtype=float)
    except (ValueError, TypeError):
        # 如果直接转换失败，逐个元素转换
        converted = []
        for v in values:
            try:
                converted.append(float(v))
            except (ValueError, TypeError):
                converted.append(np.nan)
        data = np.array(converted, dtype=float)
    
    valid_mask = np.isfinite(data)
    valid_count = np.sum(valid_mask)
    invalid_count = len(values) - valid_count
    
    nan_count = np.sum(np.isnan(data))
    inf_count = np.sum(np.isinf(data))
    
    return {
        'total_points': len(values),
        'valid_points': int(valid_count),
        'invalid_points': int(invalid_count),
        'nan_count': int(nan_count),
        'inf_count': int(inf_count),
        'valid_ratio': float(valid_count / len(values)) if len(values) > 0 else 0.0
    }

"""
异常检测相关的 API 路由
"""

from flask import Blueprint, request, jsonify
from detection.three_sigma import ThreeSigmaDetection
from detection.iqr import IQRDetection
from utils.data_cleaner import validate_data, get_data_quality_info

detection_bp = Blueprint('detection', __name__, url_prefix='/api/detection')


@detection_bp.route('/methods', methods=['GET'])
def get_methods():
    """
    获取所有支持的检测方法信息
    
    返回:
    {
        "success": true,
        "data": {
            "3sigma": {
                "name": "3-Sigma 检测",
                "description": "...",
                "params": {
                    "sigma_threshold": {...}
                }
            }
        }
    }
    """
    try:
        methods_dict = ThreeSigmaDetection.get_method_info()
        # 添加 IQR 方法
        methods_dict.update(IQRDetection.get_method_info())
        # 未来可以添加更多检测方法
        # methods_dict.update(IsolationForest.get_method_info())
        
        return jsonify({
            'success': True,
            'data': methods_dict
        })
    except Exception as e:
        print(f"Error in get_methods: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取方法信息时出错: {str(e)}'
        }), 500


@detection_bp.route('/detect', methods=['POST'])
def detect_anomalies():
    """
    应用检测方法识别异常点
    
    请求体:
    {
        "timestamps": ["2024-01-01 00:00:00", ...],
        "values": [1.0, 2.0, 3.0, ...],
        "method": {
            "type": "3sigma",
            "params": {
                "sigma_threshold": 3.0
            }
        }
    }
    
    返回:
    {
        "success": true,
        "data": {
            "timestamps": [...],
            "values": [...],
            "anomalies": [false, false, true, ...],  // 异常标记
            "anomaly_indices": [2, 5, 10, ...],      // 异常点索引
            "stats": {
                "mean": 10.5,
                "std": 2.3,
                "upper_bound": 17.4,
                "lower_bound": 3.6,
                "total_points": 1000,
                "anomaly_count": 15,
                "anomaly_ratio": 0.015
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        timestamps = data.get('timestamps', [])
        values = data.get('values', [])
        method_config = data.get('method', {})
        
        if not timestamps or not values:
            return jsonify({
                'success': False,
                'message': '缺少必要参数: timestamps 和 values'
            }), 400
        
        if len(timestamps) != len(values):
            return jsonify({
                'success': False,
                'message': 'timestamps 和 values 长度不一致'
            }), 400
        
        method_type = method_config.get('type')
        params = method_config.get('params', {})
        
        # 统一的数据验证和质量检查
        is_valid, error_message = validate_data(values)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': f'数据验证失败: {error_message}'
            }), 400
        
        # 获取数据质量信息（用于日志和统计）
        quality_info = get_data_quality_info(values)
        if quality_info['invalid_points'] > 0:
            print(f"警告: 数据包含 {quality_info['invalid_points']} 个无效值 "
                  f"(NaN: {quality_info['nan_count']}, Inf: {quality_info['inf_count']}), "
                  f"将在检测过程中处理")
        
        # 根据方法类型调用相应的检测算法
        if method_type == '3sigma':
            sigma_threshold = params.get('sigma_threshold', 3.0)
            anomalies, stats = ThreeSigmaDetection.detect(values, sigma_threshold)
        elif method_type == 'iqr':
            iqr_multiplier = params.get('iqr_multiplier', 1.5)
            anomalies, stats = IQRDetection.detect(values, iqr_multiplier)
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的检测方法: {method_type}'
            }), 400
        
        # 将数据质量信息添加到统计结果中
        stats['data_quality'] = quality_info
        
        # 获取异常点的索引
        anomaly_indices = [i for i, is_anomaly in enumerate(anomalies) if is_anomaly]
        
        return jsonify({
            'success': True,
            'data': {
                'timestamps': timestamps,
                'values': values,
                'anomalies': anomalies,
                'anomaly_indices': anomaly_indices,
                'stats': stats
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        print(f"Error in detect_anomalies: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'检测异常时出错: {str(e)}'
        }), 500

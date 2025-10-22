"""
数据预处理相关的 API 路由
"""

from flask import Blueprint, request, jsonify
from preprocessing.smoothing import DataSmoothing

preprocessing_bp = Blueprint('preprocessing', __name__, url_prefix='/api/preprocessing')


@preprocessing_bp.route('/smooth', methods=['POST'])
def apply_smoothing():
    """
    应用数据平滑
    
    请求体:
    {
        "timestamps": ["2024-01-01 00:00:00", ...],
        "values": [1.0, 2.0, 3.0, ...],
        "method": "moving_average",  // 'moving_average', 'exponential', 'gaussian'
        "window_size": 5
    }
    
    返回:
    {
        "success": true,
        "data": {
            "timestamps": [...],
            "values": [...]  // 平滑后的值
        }
    }
    """
    try:
        data = request.get_json()
        
        timestamps = data.get('timestamps', [])
        values = data.get('values', [])
        method = data.get('method', 'moving_average')
        window_size = data.get('window_size', 5)
        
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
        
        # 应用平滑
        smoothed_values = DataSmoothing.apply(values, method, window_size)
        
        # 验证结果
        import math
        if any(math.isnan(v) or math.isinf(v) for v in smoothed_values):
            return jsonify({
                'success': False,
                'message': '平滑处理产生了无效值（NaN 或 Inf），请检查输入数据'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'timestamps': timestamps,
                'values': smoothed_values
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        print(f"Error in apply_smoothing: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'处理数据时出错: {str(e)}'
        }), 500


@preprocessing_bp.route('/apply-pipeline', methods=['POST'])
def apply_pipeline():
    """
    应用预处理流程（多个方法按顺序执行）
    
    请求体:
    {
        "timestamps": ["2024-01-01 00:00:00", ...],
        "values": [1.0, 2.0, 3.0, ...],
        "methods": [
            {
                "type": "smooth",
                "params": {
                    "method": "moving_average",
                    "window_size": 5
                }
            },
            {
                "type": "smooth",
                "params": {
                    "method": "gaussian",
                    "window_size": 3
                }
            }
        ]
    }
    
    返回:
    {
        "success": true,
        "data": {
            "timestamps": [...],
            "values": [...]  // 经过所有预处理后的值
        }
    }
    """
    try:
        data = request.get_json()
        
        timestamps = data.get('timestamps', [])
        values = data.get('values', [])
        methods = data.get('methods', [])
        
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
        
        # 依次应用每个预处理方法
        processed_values = values
        for method_config in methods:
            method_type = method_config.get('type')
            params = method_config.get('params', {})
            
            if method_type == 'smooth':
                method = params.get('method', 'moving_average')
                window_size = params.get('window_size', 5)
                processed_values = DataSmoothing.apply(processed_values, method, window_size)
            # 未来可以在这里添加其他预处理方法
            # elif method_type == 'detrend':
            #     processed_values = Detrending.apply(processed_values, **params)
        
        # 验证结果
        import math
        if any(math.isnan(v) or math.isinf(v) for v in processed_values):
            return jsonify({
                'success': False,
                'message': '预处理产生了无效值（NaN 或 Inf），请检查输入数据和方法参数'
            }), 500
        
        return jsonify({
            'success': True,
            'data': {
                'timestamps': timestamps,
                'values': processed_values
            }
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        print(f"Error in apply_pipeline: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'处理数据时出错: {str(e)}'
        }), 500


@preprocessing_bp.route('/methods', methods=['GET'])
def get_methods():
    """
    获取所有支持的预处理方法信息
    
    返回:
    {
        "success": true,
        "data": {
            "smooth": {
                "moving_average": {...},
                "exponential": {...},
                "gaussian": {...}
            }
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'smooth': DataSmoothing.get_method_info()
            }
        })
    except Exception as e:
        print(f"Error in get_methods: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取方法信息时出错: {str(e)}'
        }), 500

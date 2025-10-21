"""
数据管理模块 - 处理数据文件的浏览、选择等功能
"""
from flask import Blueprint, jsonify
import os
from pathlib import Path
import json
import csv
from datetime import datetime

data_bp = Blueprint('data', __name__, url_prefix='/api/data')

# 数据目录路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
ALLOWED_EXTENSIONS = {'.csv', '.json'}


def build_file_tree(directory, relative_path=""):
    """
    递归构建文件树结构，只包含 csv 和 json 文件
    
    Args:
        directory: 目录路径
        relative_path: 相对路径（用于生成 key）
    
    Returns:
        包含文件树结构的字典列表
    """
    tree = []
    
    try:
        items = sorted(os.listdir(directory))
    except PermissionError:
        return tree
    
    for item in items:
        if item.startswith('.'):  # 跳过隐藏文件
            continue
            
        item_path = os.path.join(directory, item)
        item_relative_path = os.path.join(relative_path, item) if relative_path else item
        
        if os.path.isdir(item_path):
            # 递归获取子目录
            children = build_file_tree(item_path, item_relative_path)
            
            # 只添加包含支持文件的目录
            if children:
                tree.append({
                    'title': item,
                    'key': item_relative_path,
                    'type': 'folder',
                    'children': children,
                    'selectable': False
                })
        else:
            # 检查文件扩展名
            file_ext = os.path.splitext(item)[1].lower()
            if file_ext in ALLOWED_EXTENSIONS:
                tree.append({
                    'title': item,
                    'key': item_relative_path,
                    'type': 'file',
                    'extension': file_ext,
                    'isLeaf': True,
                    'selectable': True
                })
    
    return tree


@data_bp.route('/files', methods=['GET'])
def get_file_tree():
    """
    获取数据目录的文件树结构
    
    Returns:
        JSON格式的文件树
    """
    try:
        if not os.path.exists(DATA_DIR):
            return jsonify({
                'success': False,
                'message': 'Data directory does not exist',
                'tree': []
            }), 404
        
        tree = build_file_tree(DATA_DIR)
        
        return jsonify({
            'success': True,
            'message': 'File tree retrieved successfully',
            'tree': tree,
            'data_dir': DATA_DIR
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving file tree: {str(e)}',
            'tree': []
        }), 500


@data_bp.route('/file-info', methods=['GET'])
def get_file_info():
    """
    获取指定文件的详细信息
    
    Query Parameters:
        path: 文件相对路径
    
    Returns:
        文件的详细信息
    """
    from flask import request
    
    file_path = request.args.get('path', '')
    
    if not file_path:
        return jsonify({
            'success': False,
            'message': 'File path is required'
        }), 400
    
    full_path = os.path.join(DATA_DIR, file_path)
    
    # 安全检查：确保路径在 DATA_DIR 内
    if not os.path.abspath(full_path).startswith(os.path.abspath(DATA_DIR)):
        return jsonify({
            'success': False,
            'message': 'Invalid file path'
        }), 403
    
    if not os.path.exists(full_path):
        return jsonify({
            'success': False,
            'message': 'File not found'
        }), 404
    
    try:
        file_stats = os.stat(full_path)
        
        return jsonify({
            'success': True,
            'file_info': {
                'name': os.path.basename(full_path),
                'path': file_path,
                'size': file_stats.st_size,
                'modified_time': file_stats.st_mtime,
                'extension': os.path.splitext(full_path)[1]
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error retrieving file info: {str(e)}'
        }), 500


@data_bp.route('/read-file', methods=['GET'])
def read_file():
    """
    读取数据文件内容，支持 CSV 和 JSON 格式
    
    Query Parameters:
        path: 文件相对路径
    
    Returns:
        包含时间戳和值的数组
    """
    from flask import request
    
    file_path = request.args.get('path', '')
    
    if not file_path:
        return jsonify({
            'success': False,
            'message': 'File path is required'
        }), 400
    
    full_path = os.path.join(DATA_DIR, file_path)
    
    # 安全检查：确保路径在 DATA_DIR 内
    if not os.path.abspath(full_path).startswith(os.path.abspath(DATA_DIR)):
        return jsonify({
            'success': False,
            'message': 'Invalid file path'
        }), 403
    
    if not os.path.exists(full_path):
        return jsonify({
            'success': False,
            'message': 'File not found'
        }), 404
    
    try:
        file_ext = os.path.splitext(full_path)[1].lower()
        
        if file_ext == '.csv':
            # 读取 CSV 文件
            timestamps = []
            values = []
            
            with open(full_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    # 假设 CSV 有 timestamp 和 value 列
                    if 'timestamp' in row and 'value' in row:
                        try:
                            value = float(row['value'])
                            # 跳过 NaN 和 Infinity 值
                            if not (value != value or value == float('inf') or value == float('-inf')):
                                timestamps.append(row['timestamp'])
                                values.append(value)
                                count += 1
                        except (ValueError, TypeError):
                            # 跳过无法转换的值
                            continue
            
            return jsonify({
                'success': True,
                'data': {
                    'timestamps': timestamps,
                    'values': values,
                    'total_points': count,
                    'file_type': 'csv'
                }
            })
        
        elif file_ext == '.json':
            # 读取 JSON 文件
            import re
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 处理特殊值：NaN, Infinity, -Infinity
                # 使用正则表达式确保只替换值位置的特殊字符
                content = re.sub(r':\s*NaN\s*([,}])', r': null\1', content)
                content = re.sub(r':\s*Infinity\s*([,}])', r': null\1', content)
                content = re.sub(r':\s*-Infinity\s*([,}])', r': null\1', content)
                data = json.loads(content)
            
            # 假设 JSON 是 {timestamp: value} 格式
            if isinstance(data, dict):
                timestamps = []
                values = []
                count = 0
                
                for ts, val in sorted(data.items()):
                    # 跳过 null 值（由 NaN/Infinity 转换而来）
                    if val is None:
                        continue
                    
                    # 尝试将时间戳转换为可读格式
                    try:
                        # 如果是 Unix 时间戳
                        ts_int = int(ts)
                        dt = datetime.fromtimestamp(ts_int)
                        timestamps.append(dt.strftime('%Y-%m-%d %H:%M:%S'))
                    except:
                        # 如果不是数字时间戳，直接使用
                        timestamps.append(ts)
                    
                    try:
                        value = float(val)
                        # 再次检查是否为特殊值
                        if value != value or value == float('inf') or value == float('-inf'):
                            continue
                        values.append(value)
                        count += 1
                    except (ValueError, TypeError):
                        # 跳过无法转换为浮点数的值
                        continue
                
                return jsonify({
                    'success': True,
                    'data': {
                        'timestamps': timestamps,
                        'values': values,
                        'total_points': count,
                        'file_type': 'json'
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Unsupported JSON format'
                }), 400
        
        else:
            return jsonify({
                'success': False,
                'message': f'Unsupported file type: {file_ext}'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error reading file: {str(e)}'
        }), 500

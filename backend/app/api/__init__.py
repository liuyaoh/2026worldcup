"""
API路由模块
"""

from flask import Blueprint

predict_bp = Blueprint('predict', __name__)

from . import predict  # noqa: E402, F401

"""
Shared FastAPI dependencies — import từ đây thay vì từ auth.py trực tiếp
"""
from app.api.auth import get_current_user  # noqa: F401

# Các dependency khác sẽ thêm vào đây ở TIPs sau

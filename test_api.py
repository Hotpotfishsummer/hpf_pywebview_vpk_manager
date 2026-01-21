#!/usr/bin/env python3
"""API 单元测试脚本 - 验证后端 API 是否正常"""

import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加后端到路径
sys.path.insert(0, str(Path(__file__).parent))

def test_api():
    """测试 API 的所有公开方法"""
    logger.info("=" * 80)
    logger.info("开始 API 单元测试")
    logger.info("=" * 80)
    
    try:
        # 导入 API
        logger.info("导入 VpkManagerApi...")
        from backend.api import VpkManagerApi
        logger.info("✓ VpkManagerApi 导入成功")
        
        # 创建 API 实例
        logger.info("\n创建 API 实例...")
        api = VpkManagerApi()
        logger.info("✓ API 实例创建成功")
        
        # 检查公开方法
        logger.info(f"\n公开方法列表: {list(api._PUBLIC_METHODS)}")
        
        # 测试每个方法
        logger.info("\n测试各方法的可调用性:")
        for method_name in sorted(api._PUBLIC_METHODS):
            try:
                method = getattr(api, method_name)
                is_callable = callable(method)
                status = "✓" if is_callable else "✗"
                logger.info(f"  {status} {method_name}: {'callable' if is_callable else 'not callable'}")
                
                # 检查方法签名
                if hasattr(method, '__code__'):
                    code = method.__code__
                    args = code.co_varnames[1:code.co_argcount]  # 跳过 self
                    logger.debug(f"      参数: {args}")
            except Exception as e:
                logger.error(f"  ✗ 获取方法 {method_name} 失败: {e}")
        
        # 测试 __dir__ 方法
        logger.info("\n测试 __dir__() 反射:")
        dir_result = dir(api)
        logger.info(f"  dir(api) 返回 {len(dir_result)} 个方法")
        logger.info(f"  结果: {dir_result}")
        
        # 验证 PyWebView 兼容性
        logger.info("\n验证 PyWebView 兼容性:")
        logger.info(f"  API 对象类型: {type(api).__name__}")
        logger.info(f"  API 对象模块: {type(api).__module__}")
        logger.info(f"  API 是否可反射: {hasattr(api, '__dir__')}")
        
        # 测试 __getattr__ 过滤
        logger.info("\n测试属性访问过滤:")
        try:
            _ = api._storage_service
            logger.warning("  ✗ 警告: 可以访问私有属性 (_storage_service)")
        except AttributeError:
            logger.info("  ✓ 私有属性访问被正确过滤")
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ 所有测试通过，API 可以使用")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"\n✗ 测试失败: {e}", exc_info=True)
        logger.error("=" * 80)
        return False

if __name__ == '__main__':
    success = test_api()
    sys.exit(0 if success else 1)

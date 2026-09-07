"""VPK 核心操作相关的 API 方法(mixin)。

由 backend/api.py 的 VpkManagerApi 继承使用;依赖宿主提供的各服务
(scan/export/import/localize/metadata/storage/config)与 _is_scanning/_is_exporting 状态。
"""

import logging
import os
from typing import List

import webview

logger = logging.getLogger(__name__)


class VpkOpsApiMixin:
    """向 PyWebView 前端暴露的 VPK 扫描/导出/删除/导入/本地化方法"""

    def scan_vpk_files(self, directory: str) -> dict:
        """扫描目录以查找 VPK 文件。

        参数:
            directory: L4D2 根目录路径

        返回:
            包含成功状态和本地/创意工坊 VPK 文件列表的字典
        """
        if self._is_scanning:
            return {
                "success": False,
                "error": "扫描已在进行中",
                "local_vpks": [],
                "workshop_vpks": [],
            }

        try:
            self._is_scanning = True
            logger.info(f"扫描 VPK 文件: {directory}")

            # 验证目录
            if not os.path.isdir(directory):
                return {
                    "success": False,
                    "error": f"目录不存在: {directory}",
                    "local_vpks": [],
                    "workshop_vpks": [],
                }

            # 保存目录供以后使用
            self.storage_service.save_l4d2_directory(directory)

            # 自动应用配置
            self.config_service.apply_autoexec_template(directory)

            # 扫描本地与创意工坊 VPK 文件
            scan_result = self.scan_service.scan(directory)

            return {
                "success": True,
                "local_vpks": scan_result["local_vpks"],
                "workshop_vpks": scan_result["workshop_vpks"],
            }

        except Exception as e:
            logger.error(f"扫描 VPK 文件出错: {e}")
            return {
                "success": False,
                "error": str(e),
                "local_vpks": [],
                "workshop_vpks": [],
            }
        finally:
            self._is_scanning = False

    def export_vpks(self, file_paths: List[str], output_dir: str, better_naming: bool = False, overwrite: bool = False) -> dict:
        """将选定的 VPK 文件导出到压缩归档。

        参数:
            file_paths: 要导出的 VPK 文件路径列表
            output_dir: 保存导出归档的目录
            better_naming: 是否在压缩包内重命名文件
            overwrite: 是否覆盖已存在的目标文件

        返回:
            包含成功状态和导出详情的字典;目标已存在时返回 exists=True
        """
        if self._is_exporting:
            return {
                "success": False,
                "error": "导出已在进行中",
            }

        try:
            self._is_exporting = True
            logger.info(f"开始导出 {len(file_paths)} 个 VPK 文件")

            # 提取文件标题用于压缩包命名
            titles = []
            for path in file_paths:
                title = self.metadata_service.get_addontitle(path)
                titles.append(title)

            # 直接运行，pywebview 会在单独的线程中调用此方法
            result = self.export_service.export_vpks(
                file_paths,
                output_dir,
                titles=titles,
                better_naming=better_naming,
                overwrite=overwrite,
            )

            return {
                "success": True,
                "message": f"导出完成: {result}",
                "file_path": result,
            }

        except FileExistsError as e:
            logger.warning(f"导出目标文件已存在: {e}")
            return {
                "success": False,
                "exists": True,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"导出 VPK 文件出错: {e}")
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            self._is_exporting = False

    def delete_vpk_file(self, file_path: str, disable: bool = True) -> dict:
        """删除或禁用 VPK 文件。

        参数:
            file_path: VPK 文件路径
            disable: 如果为 True，重命名为 .vpk.disabled；如果为 False，删除

        返回:
            包含成功状态的字典
        """
        try:
            logger.info(
                f"{'禁用' if disable else '删除'} VPK 文件: {file_path}"
            )
            self._disable_or_delete_single(file_path, disable)
            return {"success": True, "message": f"文件{'禁用' if disable else '删除'}成功"}
        except Exception as e:
            logger.error(f"处理 VPK 文件出错: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _disable_or_delete_single(file_path: str, disable: bool) -> None:
        """禁用/删除单个 VPK 文件及其关联图片，失败时抛异常。

        与批量版行为一致：对已 .disabled 的文件执行 disable 是 toggle
        （移除后缀恢复启用）；重命名/删除 VPK 时同步处理同名
        .jpg/.png/.jpeg/.txt 文件。
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if disable:
            if file_path.endswith(".disabled"):
                new_path = file_path[:-9]  # 启用: 移除 .disabled
            else:
                new_path = f"{file_path}.disabled"

            # 同步重命名关联的图片/文本文件
            old_base = os.path.splitext(file_path)[0]
            new_base = os.path.splitext(new_path)[0]
            for ext in ['.jpg', '.png', '.jpeg', '.txt']:
                old_img = old_base + ext
                new_img = new_base + ext
                if os.path.exists(old_img):
                    if os.path.exists(new_img):
                        os.remove(new_img)
                    os.rename(old_img, new_img)

            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(file_path, new_path)
        else:
            # 同步删除关联的图片/文本文件
            base_stem = os.path.splitext(file_path)[0]
            for ext in ['.jpg', '.png', '.jpeg', '.txt']:
                img_path = base_stem + ext
                if os.path.exists(img_path):
                    os.remove(img_path)
            os.remove(file_path)

    def enable_vpk_file(self, file_path: str) -> dict:
        """通过移除 .disabled 后缀启用禁用的 VPK 文件。

        参数:
            file_path: 禁用的 VPK 文件路径 (.vpk.disabled)

        返回:
            包含成功状态的字典
        """
        try:
            logger.info(f"启用 VPK 文件: {file_path}")

            if not os.path.exists(file_path):
                return {"success": False, "error": f"文件不存在: {file_path}"}

            if not file_path.endswith(".disabled"):
                return {"success": False, "error": "文件未被禁用"}

            # 移除 .disabled 后缀
            new_path = file_path[:-9]  # 移除 ".disabled" (9 个字符)
            if os.path.exists(new_path):
                return {"success": False, "error": f"文件已存在: {new_path}"}

            os.rename(file_path, new_path)
            logger.info(f"成功启用 VPK 文件: {new_path}")
            return {"success": True, "message": "文件启用成功"}

        except Exception as e:
            logger.error(f"启用 VPK 文件出错: {e}")
            return {"success": False, "error": str(e)}

    def delete_multiple_vpk_files(self, file_paths: List[str], disable: bool = True) -> dict:
        """删除或禁用多个 VPK 文件。

        参数:
            file_paths: VPK 文件路径列表
            disable: 如果为 True，重命名为 .vpk.disabled；如果为 False，删除

        返回:
            包含成功状态和计数的字典
        """
        try:
            logger.info(
                f"{'禁用' if disable else '删除'} {len(file_paths)} 个 VPK 文件"
            )

            success_count = 0
            error_count = 0
            errors = []

            for file_path in file_paths:
                try:
                    self._disable_or_delete_single(file_path, disable)
                    success_count += 1
                    logger.info(f"Successfully {'disabled' if disable else 'deleted'} {file_path}")

                except Exception as e:
                    error_count += 1
                    errors.append(f"Error processing {file_path}: {str(e)}")
                    logger.error(f"Error processing {file_path}: {e}")

            return {
                "success": error_count == 0,
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors,
                "message": f"Processed {success_count} files successfully, {error_count} errors",
            }

        except Exception as e:
            logger.error(f"Error deleting multiple VPK files: {e}")
            return {"success": False, "error": str(e)}

    def import_compressed_vpks(self) -> dict:
        """打开文件对话框选择压缩包，并导入其中的 VPK。"""
        try:
            if not self._window:
                return {"success": False, "error": "WebView 窗口未就绪"}

            # 获取当前 L4D2 目录以确定 addons 文件夹
            l4d2_dir = self.storage_service.get_l4d2_directory()
            if not l4d2_dir:
                return {"success": False, "error": "请先选择 L4D2 安装目录"}

            addons_dir = os.path.join(l4d2_dir, "left4dead2", "addons")
            if not os.path.exists(addons_dir):
                return {"success": False, "error": f"addons 目录不存在: {addons_dir}"}

            # 1. 选择文件
            file_types = ('Addon Archives (*.zip;*.7z;*.zst)', 'All files (*.*)')
            result = self._window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=True,
                file_types=file_types
            )

            if not result:
                return {"success": True, "message": "用户取消了选择", "imported_count": 0}

            # 2. 调用导入服务
            import_result = self.import_service.import_compressed_files(result, addons_dir)
            
            # 如果成功，自动重新扫描一下
            if import_result.get("success") or import_result.get("imported_count", 0) > 0:
                logger.info(f"导入完成，成功导入了 {import_result.get('imported_count')} 个压缩包中的文件")

            return import_result

        except Exception as e:
            logger.error(f"导入压缩包出错: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def localize_workshop_vpks(self, file_paths: List[str], better_naming: bool = False) -> dict:
        """将选定的创意工坊 VPK 文件本地化（复制到 addons 目录）。"""
        try:
            if not file_paths:
                return {"success": False, "error": "未选择文件"}

            l4d2_dir = self.storage_service.get_l4d2_directory()
            if not l4d2_dir:
                return {"success": False, "error": "未找到 L4D2 目录"}

            addons_dir = os.path.join(l4d2_dir, "left4dead2", "addons")
            if not os.path.exists(addons_dir):
                os.makedirs(addons_dir, exist_ok=True)

            return self.localize_service.localize(file_paths, l4d2_dir, better_naming)
        except Exception as e:
            logger.error(f"本地化创意工坊文件出错: {e}")
            return {"success": False, "error": str(e)}

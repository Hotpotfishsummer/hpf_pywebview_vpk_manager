import type { VpkFile } from '@/stores/vpk-manager'

/**
 * 后端 API 返回结果的类型定义。
 * 字段与 backend 各 service/api 的返回 dict 一一对应;
 * 标注为可选是因为失败分支通常只带 success/error。
 */

export interface ApiResult {
  success: boolean
  error?: string
  message?: string
}

/** scan_vpk_files */
export interface ScanResult extends ApiResult {
  local_vpks: VpkFile[]
  workshop_vpks: VpkFile[]
}

/** import_compressed_vpks */
export interface ImportResult extends ApiResult {
  imported_count?: number
  errors?: string[] | null
}

/** localize_workshop_vpks */
export interface LocalizeResult extends ApiResult {
  success_count?: number
  errors?: string[] | null
}

/** export_vpks */
export interface ExportResult extends ApiResult {
  file_path?: string
  /** 目标归档已存在且未指定 overwrite 时为 true,由前端决定是否覆盖重试 */
  exists?: boolean
}

/** 远程 SFTP 文件条目(sftp_service.list_vpk_files) */
export interface RemoteFile {
  name: string
  path: string
  size: number
  modified_time: number
  is_disabled: boolean
}

/** list_remote_vpks */
export interface RemoteListResult extends ApiResult {
  files?: RemoteFile[]
}

/** delete_multiple_vpk_files(本地批量)与 delete_multiple_remote_vpks(远程批量) */
export interface BatchDeleteResult extends ApiResult {
  success_count?: number
  error_count?: number
  errors?: string[]
}

/** download_remote_vpks */
export interface DownloadResult extends ApiResult {
  downloaded_count?: number
}

/** upload_local_vpks */
export interface UploadResult extends ApiResult {
  uploaded_count?: number
}

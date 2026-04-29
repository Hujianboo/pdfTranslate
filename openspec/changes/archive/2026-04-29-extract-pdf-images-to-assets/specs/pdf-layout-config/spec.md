## MODIFIED Requirements

### Requirement: 配置保留图片块定位信息
系统 SHALL 将 PDF 页面中的图片对象记录为图片块，并为每个图片块输出稳定 ID、bbox 坐标、页面编号、图片尺寸、可追踪引用，以及在资源已提取时可用于重建渲染的图片资产路径。

#### Scenario: 图片块包含后续重建所需字段
- **GIVEN** 一个 PDF 页面包含图片对象
- **WHEN** 系统将其解析为 layout/config
- **THEN** 页面中的每个图片块包含 `id`、`kind`、`page_number`、`bbox` 和 `image` 字段，且 `kind` 等于 `image`

#### Scenario: 图片块 ID 稳定且可追踪
- **GIVEN** 同一个包含图片的 PDF 输入文件
- **WHEN** 系统连续两次解析为 layout/config
- **THEN** 两次输出中同一页面同一顺序图片块的 `id` 完全一致，并采用 `p<page>_i<image>` 格式

#### Scenario: 图片块保留尺寸和引用信息
- **GIVEN** 一个图片块来自 PDF 页面上的图片对象
- **WHEN** 系统将其解析为 layout/config
- **THEN** 该图片块的 `image` 对象包含数值型 `width`、`height` 和字符串型 `ref` 字段，且 `width` 和 `height` 均大于 `0`

#### Scenario: 图片块记录已提取资产路径
- **GIVEN** 一个图片块已成功关联到导出的图片资产
- **WHEN** 系统输出增强版 layout/config
- **THEN** 该图片块的 `image` 对象包含字符串型 `asset_path` 字段，且该路径指向存在的本地图片文件

#### Scenario: 图片资产路径是可选字段
- **GIVEN** 一个图片块尚未关联到导出的图片资产
- **WHEN** 系统输出 layout/config
- **THEN** 该图片块的 `image` 对象可以不包含 `asset_path` 字段，并且仍然符合 LayoutConfig schema

# astropy

> 天文学核心 Python 库：坐标变换、单位与物理量、FITS 文件、宇宙学计算、精确时间、表格数据、天文图像处理。

## 1. 一句话理解

`astropy` 是**天文学的 NumPy**——它不是单一算法，而是一套按数据对象分区的工具箱：物理量（`Quantity`）、天球坐标（`SkyCoord`）、时间（`Time`）、FITS、表格（`Table`）、宇宙学模型、WCS 图像坐标，各自一个 reference。

## 2. 它解决什么问题

天文数据有几个独特的坑：物理量带单位、坐标有多套 frame（ICRS/Galactic/FK5/AltAz）、时间有多个 scale（UTC/TAI/TT/TDB）和 format（JD/MJD/ISO）、FITS 是天文专用文件格式。用普通 NumPy/datetime 处理这些会错得悄无声息。`astropy` 把单位、坐标、时间都变成"带语义的对象"，让换算和转换显式、可校验。

## 3. 核心心智模型

**按对象分区，按"单位/坐标 → 数据文件 → 表格或模型 → 验证"的顺序衔接。** 先判断手里是什么对象，再进对应 reference：

- 带单位的量 → `Quantity`，`.to()` 换算，注意 equivalency（光谱/Doppler）与对数单位（mag/dB/dex）。
- 天球坐标 → `SkyCoord` 做 frame 变换；涉及 AltAz 必须同时给 `obstime` + `EarthLocation`。
- 时间 → `Time` 管 format 与 scale 两个正交维度，`TimeDelta` 管加减。
- FITS → `fits.open()` 上下文，先看 HDU 结构再读 `data`/`header`。
- 表格 → `Table`/`QTable`，支持跨格式读写（FITS/CSV/HDF5/VOTable/Parquet）。
- WCS → `pixel_to_world`/`world_to_pixel`，配合 NDData/CCDData 绑定数据+单位+不确定度+mask。

## 4. 一次典型运转

处理一张 FITS 图像的坐标标注：`fits.open()` 读 HDU → 从 header 建 `WCS` → `pixel_to_world` 转天球坐标 → 用 `SkyCoord` 和 `Time`（带 `obstime`）做进一步分析 → 用 `Quantity` 保留单位算距离/亮度。

## 5. 何时用 / 何时不用

**用**：天文坐标变换、单位换算、FITS 读写、宇宙学距离/年龄、时间尺度转换、星表操作、像素—世界坐标变换。

**不用**：普通 NumPy、普通 CSV、非天文学的日期运算——用更匹配的工具。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 附属 7 个专题 reference：units / coordinates / cosmology / fits / tables / time / wcs_and_other_modules。

## 7. 易错点与坑

- **AltAz 缺 obstime/location**：没有观测时间与地点，AltAz 结果不能当作有效观测坐标。
- **时间忘区分 format 和 scale**：JD/MJD/ISO 与 UTC/TAI/TT 不是同一维度。
- **FITS 只改内存不写回**：写回要明确 `overwrite` 与扩展位置，否则没持久化。
- **逐行追加表格**：大批量加行要一次性构造，避免性能问题。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/astropy/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）

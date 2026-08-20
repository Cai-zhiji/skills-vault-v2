# timesfm-forecasting

> Google TimesFM 零样本时间序列预测：无需训练，喂任意单变量序列，返回点预测 + 校准的分位数预测区间。

## 1. 一句话理解

`timesfm-forecasting` 包装 Google Research 的 **TimesFM 基础模型**做零样本预测——不训练自定义模型，直接喂序列得到带校准预测区间的概率预测。它的特色是**强制预检脚本**，在加载模型前先验 RAM/GPU/磁盘，避免 agent 把用户机器跑崩。

## 2. 它解决什么问题

传统时间序列预测（ARIMA/ETS）要手工调参、逐序列建模。TimesFM 用基础模型零样本预测任意单变量序列，还带校准的区间，适合销售/需求/传感器/体征/价格/天气等。

## 3. 核心心智模型

**零样本基础模型 + 强制系统预检。** 关键数字：TimesFM 2.5 用 200M 参数（磁盘 ~800MB，CPU 上 RAM ~1.5GB，GPU ~1GB VRAM）；归档的 v1/v2 500M 模型需 ~32GB RAM。**永远先跑系统检查器**。

**适用**：任意单变量序列、零样本、概率预测、任意长度（1–16,384 上下文点）、批量预测成百上千序列、要基础模型而非手调参数。**不适用**：需训练自定义模型、多变量/协变量场景（部分情况）。

## 4. 一次典型运转

先跑预检（验 RAM/GPU/磁盘）→ 装 TimesFM → 喂 CSV/DataFrame/数组 → 得点预测 + 分位数区间。

## 5. 何时用 / 何时不用

**用**：任意单变量序列零样本预测、概率区间、批量预测、要基础模型方案。

**不用**：需要训练自定义模型、纯多变量/强协变量场景。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 依赖 TimesFM 模型权重（磁盘 ~800MB），含系统预检脚本。

## 7. 易错点与坑

- **跳过预检**：模型会吃内存，必须先跑系统检查器，否则可能崩机。
- **拿 v1/v2 大模型**：500M 版本要 ~32GB RAM，优先 2.5 的 200M。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/timesfm-forecasting/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）

# networkx

> 复杂网络与图分析的 Python 工具：创建、分析、可视化，最短路径、中心性、社区检测、合成网络生成。

## 1. 一句话理解

`networkx` 是**图与网络的 NumPy**：创建、操作、分析图结构——社交网络、生物网络、交通系统、引用网络、知识图谱，任何"实体间关系"的场景都适用。

## 2. 它解决什么问题

很多系统本质是图（节点 + 边），但通用工具没有图算法。`networkx` 提供图的创建、算法（Dijkstra、PageRank、最小生成树、最大流）、中心性度量、社区检测、合成网络生成、可视化。

## 3. 核心心智模型

**四种图类型**：`Graph`（无向单边）、`DiGraph`（有向）、`MultiGraph`（多重边）、`MultiDiGraph`。能力分块：图创建与操作（节点可任意 hashable、带属性边）、图算法（最短路径/中心性/聚类/社区）、网络生成（随机/无标度/小世界）、图 I/O（edge list/GraphML/JSON/CSV/邻接矩阵）、可视化（matplotlib 或交互库）。

## 4. 一次典型运转

建图 → 加节点/边（带属性）→ 跑中心性或最短路径 → 社区检测 → 可视化或导出。

## 5. 何时用 / 何时不用

**用**：图/网络数据结构、关系分析、图算法、社区检测、合成网络、网络可视化。

**不用**：非关系型数据分析（普通 DataFrame 场景）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。

## 7. 易错点与坑

- **方向搞错**：有向关系要用 `DiGraph`，别用无向 `Graph` 糊弄。
- **大规模图用纯 Python 太慢**：超大图考虑 graph-tool/igraph。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/networkx/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）

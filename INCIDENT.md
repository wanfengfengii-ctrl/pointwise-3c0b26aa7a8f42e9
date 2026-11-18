# 涂层厚度复测交班事故

`sample.json` 的原版含同线速试片 A 和 B，偏差分别为 −1 与 1 微米。待测片线速相同，申请门槛 `k=2`。事故脚本为原版冻结校准，停用测量来源，关闭并重开数据库，再凭该校准号签发和读回报告。

正确报告包含闭区间 `[−3,3]`，导出的 `candidate_regions` 为 `[[[-3,1],[3,1]]]`。候选 2 与 3 均合格，4 不合格。按 A、B、待测片的顺序，候选 2 对应残差 `(-5/3, 1/3, 4/3)`。候选 3 对应残差 `(-2, 0, 2)`，A 与待测片的绝对残差并列，两片均计入。独立的完整封存件也应签发相同区间。

在仓库根目录按 README.md 的 Python 环境运行。

```sh
python3 -B -m incident
python3 -B -m verify
python3 -B -m demo
```

`incident` 打印实际和预期的区间及三点归属。业务结果不一致时打印 `THICKNESS_SET_MISMATCH` 并退出 1，一致时退出 0。`verify` 运行完整原回归，`demo` 展示更正、停用、重开和续签的实际报告。`.pointwise-runtime.json` 保存现有命令行运行清单，`version` 为 1、`kind` 为 `cli`、`setup` 为准备命令的 argv 列表，`verify` 与 `demo` 分别是核验和演示命令的 argv。

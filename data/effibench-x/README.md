# EffiBench-X inputs

`python_tasks.csv` and `cpp_tasks.csv` hold the 623 tasks per language that
every method in the paper optimized:

- `problem_id`: EffiBench-X task id
- `description`: problem statement
- `canonical_solution`: the program each method was asked to optimize

They come from [EffiBench-X](https://github.com/EffiBench/EffiBench-X)
([dataset](https://huggingface.co/datasets/EffiBench/effibench-x),
[paper](https://arxiv.org/abs/2505.13004)) and are redistributed
under the Apache License 2.0. The statements match the public dataset. The
input programs differ from every public dataset revision for 210 Python and
161 C++ tasks, so the exact programs used in the paper are included here.

Test cases are not included. Get them from the upstream dataset.

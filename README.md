# Advent of Code, by GPT-3

This solves [Advent of Code](https://adventofcode.com/) puzzles by having GPT-3 write code in response to the
puzzle's input.

I placed 1st on Day 4 Part 1 (2022) with this code, and 2nd on Day 3 Part 1 (2022) with a
previous version.

## Table of Contents

- [How it works](#how-it-works)
- [How to use](#how-to-use)
- [Installation](#installation)

## How it works

The code is written in Python, and uses the OpenAI API to call GPT-3.
It also uses the `aoc-cli` library to download the puzzle input and submit the answer.

## How to use

```bash
python3 openai.py --day=2
```

All flags:

- `--day` **(required)** - The day of the puzzle.
- `--year` - The year of the puzzle. Defaults to the current year.
- `--part` - The part of the puzzle.
- `--n-workers` - The number of workers to use. Defaults to 1
- `--runs` - The number of runs to make. Defaults to 200
- `--stop-when-submitted` - Stop when the answer is submitted. Defaults to False

Example:

```bash
python3 openai.py --day=2 --year=2019 --runs=10
```

## Installation

### Install aoc-cli

All instructions can be found in the [aoc-cli repo](https://github.com/scarvalhojr/aoc-cli)

Install the `aoc-cli` library:

```bash
cargo install aoc-cli
# or
brew install scarvalhojr/tap/aoc-cli
# or, for Windows
winget install aoc-cli
```

And [add the AOC session cookie](https://github.com/scarvalhojr/aoc-cli#session-cookie).

### Install OpenAI API

Install the `openai` library:

```bash
pip install openai
```

Add an [OpenAI API key](https://beta.openai.com/account/api-keys) to the
`OPENAI_API_KEY` environment variable.

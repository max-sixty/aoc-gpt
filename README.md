# Advent of Code, by GPT-3

This solves Advent of Code puzzles by having GPT-3 write code in response to the
puzzle's input.

I placed 1st on Day 4 Part 1 (2022) with this code, and 2nd on Day 3 Part 1 (2022) with a
previous version.

# Table of Contents

- [How it works](#how-it-works)
- [How to use](#how-to-use)
- [Installation](#installation)

# How it works

The code is written in Python, and uses the OpenAI API to call GPT-3.
It also uses the `aoc` library to download the puzzle input and submit the answer.

# How to use

```bash
$ python3 openai.py --day 2
```

All flags:

* `--day` **(required)** - The day of the puzzle.
* `--year` - The year of the puzzle. Defaults to the current year.
* `--part` - The part of the puzzle.
* `--n-workers` - The number of workers to use. Defaults to 1
* `--runs` - The number of runs to make. Defaults to 200
* `--stop-when-submitted` - Stop when the answer is submitted. Defaults to False

Example:

```bash
$ python3 openai.py --day 2 --year 2019 --runs 10
```

# Installation

Install the `aoc` library:

    # cargo install aoc-cli

    or

    # brew install scarvalhojr/tap/aoc-cli

    or

    # winget install aoc-cli


> Different Advent of Code users get different puzzle input. To download your input and submit your answer, you need an adventofcode.com session cookie. To obtain your session cookie, login to the Advent of Code website and inspect the session value of the cookie that gets stored in your browser. Put the session number (a long hex string) in a file called .adventofcode.session in your home directory. This file should only contain your session number, in a single line.

Install the `openai` library:

    pip install openai

> Add your OpenAI API key to the `OPENAI_API_KEY` environment variable.


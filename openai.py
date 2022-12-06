from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
import textwrap
from concurrent import futures
from contextlib import redirect_stdout
from functools import partial
from pathlib import Path
from typing import Counter, Iterable

import click

logger = logging.getLogger(__name__)

logging.basicConfig()

LLM_COMMAND_PREFIX = (
    f"openai api completions.create --engine=text-davinci-003 --max-tokens=2000 -p "
)

RESPONSES_PATH = "llm_responses"
REQUESTS_PATH = "llm_requests"
OUTPUTS_PATH = "python_outputs"
PUZZLE_FILE = "puzzle.md"

THRESHOLD = 2


def year_day_path(year: int, day: int) -> Path:
    return Path(f"{year}-{day}")


def write_instructions(day: int, year: int) -> None:
    subprocess.run(
        f"aoc download --overwrite --input-file=input.txt --day={day} --year={year}",
        shell=True,
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    subprocess.run(
        f"aoc read --overwrite --puzzle-file=puzzle.md --day={day} --year={year}",
        shell=True,
        capture_output=True,
        check=True,
        text=True,
    ).stdout


def read_instructions(day: int) -> str:
    return Path(PUZZLE_FILE).read_text()


def extract_part_1(text):
    text = re.sub(".*--- Day.*", "", text)
    text = re.sub(".*-----", "", text)
    text = re.sub("\\--- Part", "--- Part", text)
    text = text.replace("\n\n\n", "\n")
    text, _ = re.subn("Your puzzle answer was.*", "", text)
    return text.split(r"\--- Part Two ---")[0]


def extract_part_2(text):
    text = re.sub(".*--- Day.*", "", text)
    text = re.sub(".*-----", "", text)
    text, _ = re.subn("Your puzzle answer was.*", "", text)
    # awkward way of transforming `   \--- Part Two ---` into `--- Part Two ---`
    text = re.sub(r"(.*)\\(--- Part)", r"\1\2", text)

    text = text.split("If you still want to see it,")[0]
    text = text.split("Both parts of this puzzle are complete")[0].strip()

    # There's no Part One, only a Part Two, so we add in that to make it clearer
    #
    # TODO: weirdly this once caused it to do much worse. Need to test that; it's
    # very possible it's something else that caused it.
    return f"--- Part One ---\n\n{text}"


def amend_instructions(text, part):

    # Telling it it's an AoC problem seems to help slightly (I got that advice from
    # GPT-Chat, no joke)
    #
    # Adding "difficult" seemed to help at one point, but doesn't seem to any longer
    llm_prefix = (
        "Here's an Advent of Code puzzle, which is a cryptic puzzle told through "
        "an imaginary story. You need to write code which solves it. The description "
        "includes an example of solving a simplified version of the puzzle.\n\n-----\n"
    )
    # "with any relevant details on the same line" seems to help (without saying the
    # same line, it'll do things like print every value as it's looping).
    llm_instructions = (
        f"Now write python3 code which prints the correct answer"
        f"{'' if part == 1 else ' to Part Two'}. "
        "Print any information which supports your answer on the same line as the answer. "
        "The input is in a file `input.txt`. "
        "\n\n"
        "```python"
    )
    # I also tried prompts like these, but they didn't seem to work as well:
    #
    # This is a difficult problem! Think about it carefully, step-by-step. If you're not \
    # confident, have the python print "I'm not confident" instead.
    #         llm_instructions = f"""
    # Write python3 code which prints the correct answer{'' if part == 1 else ' to Part Two'}, \
    # as a sentence. Include any other useful numbers in the sentence. The input is in a
    # file `input.txt`.
    #
    # It might be more difficult than it looks, so go step-by-step.

    # ```python
    # """

    text = f"{llm_prefix}{textwrap.indent(text, '    ')}\n\n-----\n\n{llm_instructions}"
    (Path(REQUESTS_PATH) / f"part-{part}.txt").write_text(text)
    return shlex.quote(text)


def do_part(n: int, day: int, part: int) -> str | None:
    # TODO: this part can be split up; doesn't need to be done by each process (but it's
    # fast so not a big impact)
    instructions = read_instructions(day)
    if part == 1:
        instructions = amend_instructions(extract_part_1(instructions), part=part)
    elif part == 2:
        instructions = amend_instructions(extract_part_2(instructions), part=part)
    else:
        raise ValueError

    try:
        llm_response = request_python_from_llm(instructions)
    except Exception as e:
        print(f"Run {n} didn't generate a python excerpt")
        logger.info(f"Run {n} didn't generate a python excerpt")
        (Path(RESPONSES_PATH) / f"part_{part}_{n}.error").write_text(str(e))
        return None
    (Path(RESPONSES_PATH) / f"part_{part}_{n}.py").write_text(llm_response)
    try:
        # Run the code, writing the output to a file
        f = Path(OUTPUTS_PATH) / f"part_{part}_{n}.txt"
        with redirect_stdout(f.open("w+")):
            exec(llm_response)
        return f.read_text()
    except Exception as e:
        print(f"Run {n} failed with `{e}`")
        logger.info(f"Run {n} failed with `{e}`")
        return None


def request_python_from_llm(instructions) -> str:
    llm_command = f"{LLM_COMMAND_PREFIX} {instructions}"

    llm_respose = subprocess.run(
        llm_command,
        shell=True,
        capture_output=True,
        text=True,
    )
    if llm_respose.returncode == 0:
        try:
            return llm_respose.stdout.split("```python")[1].split("```")[0]
        except Exception:
            raise ValueError(
                f"Couldn't parse python from LLM: {llm_respose.stdout}, {llm_respose.stderr}"
            )
    else:
        raise ValueError(
            f"Error code from openai: {llm_respose.stdout}, {llm_respose.stderr}"
        )


def parse_answer(text) -> Iterable[str]:
    """
    Returns an iterable of the numbers from the first line
    """
    if not text:
        return []
    # Only grab the first line. Some scripts will write lots, but most only
    # write one (we ask it to only write one).
    line = text.splitlines()[0]
    numbers = re.search(r"(\d+)", line)
    if numbers and len(numbers.groups()) < 10:
        # Sometimes there are multiple numbers; include all of them as long as there
        # aren't like 10
        answers = numbers.groups()
        # Also filter out `0` and `1` as they're probably mistakes
        for answer in answers:
            if answer not in ("0", "1"):
                yield answer
    else:
        return []


def read_results(part: int) -> Counter:
    c: Counter = Counter()
    for n in range(1, 100):
        f = Path(OUTPUTS_PATH) / f"part_{part}_{n}.txt"
        if not f.exists():
            continue
        answer = parse_answer(f.read_text())
        if answer:
            c.update(answer)

    return c


def submit_result(day, year, part, answer):
    logger.info(f"Submitting {answer} for part {part}")
    return subprocess.run(
        f"aoc submit --day={day} --year={year} {part} {answer}",
        shell=True,
        capture_output=True,
        check=True,
        text=True,
    ).stdout


def run_parallel(
    day: int,
    year: int,
    part: int,
    stop_when_submitted: bool,
    n_workers: int,
    runs: int,
    threshold: int = THRESHOLD,
):

    print(f"Starting {n_workers} workers")
    c: Counter = Counter()
    submitted = False
    func = partial(do_part, day=day, part=part)
    with futures.ProcessPoolExecutor(max_workers=n_workers) as executor:

        fs = []

        # If we can't do it in 200 runs, we're probably not going to do it at all
        for n in range(runs):
            fs.append(executor.submit(func, n))

        for f in futures.as_completed(fs):
            result = f.result()
            logger.debug(f"Got result {result}")
            answer = parse_answer(result)
            if answer:
                c.update(answer)
            if submitted:
                print(
                    f"Already submitted but continuing collecting results. Current counts: {c}"
                )
                continue

            # Only submit if the top answer is 2 or more above the next answer
            top_results = c.most_common(2)
            if len(top_results) >= 1:
                top = top_results[0][1]
                # Only one result, so use zero for next
                next = top_results[1][1] if len(top_results) == 2 else 0
                if top - next >= threshold:
                    print(f"Submitting {top_results[0][0]}. Counts were {c}")
                    out = submit_result(day, year, part, c.most_common(1)[0][0])
                    print(out)
                    submitted = True
                    if stop_when_submitted:
                        print(f"Now stopping on part {part}. Final results: {c}")
                        # We can't seem to cancel everything, so this hangs until all
                        # the running futures are complete. That's annoying when we want
                        # to start part 2 after submitting part 1. Looks not that easy
                        # to do
                        # https://stackoverflow.com/questions/29177490/how-do-you-kill-futures-once-they-have-started
                        executor.shutdown(wait=False, cancel_futures=True)
                        return
            print(f"No answer hit the threshold, not submitting. Current counts: {c}")
        print(f"Reached all attempts without success, stopping. Final results: {c}")
        return


def get_year():
    return int(
        subprocess.run("date +%Y", shell=True, capture_output=True, text=True).stdout
    )


@click.command()
@click.option("--part", type=int)
@click.option("--day", type=int, required=True)
@click.option("--year", type=int, required=False, default=get_year())
@click.option("--n-workers", type=int, default=1)
@click.option("--runs", type=int, required=False, default=200)
@click.option("--stop-when-submitted", is_flag=True)
def run(
    day: int, year: int, part: int, n_workers: int, runs: int, stop_when_submitted: bool
) -> None:

    print(f"Running {part=}, {day=}, {year=}")

    year_day_path(year, day).mkdir(exist_ok=True)
    (year_day_path(year, day) / RESPONSES_PATH).mkdir(exist_ok=True)
    (year_day_path(year, day) / OUTPUTS_PATH).mkdir(exist_ok=True)
    (year_day_path(year, day) / REQUESTS_PATH).mkdir(exist_ok=True)
    # Slightly hacky way to make the day path local; which for executing the python is
    # important, becasue we don't want to confuse the AI by giving it a more complicated
    # path than `input.txt`.
    os.chdir(year_day_path(year, day))

    write_instructions(day, year)

    if part is None:
        run_parallel(day, year, 1, stop_when_submitted, n_workers, runs)
        run_parallel(day, year, 2, stop_when_submitted, n_workers, runs)
    else:
        if n_workers == 1:
            do_part(0, day, part)
        else:
            run_parallel(day, year, part, stop_when_submitted, n_workers, runs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    run()

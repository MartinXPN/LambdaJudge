import os
import ujson as json


def main():
    files = [file for file in os.listdir() if file.endswith(".txt")]

    for file in files:
        with open(file, "r") as f:
            text = f.read()
        tests = text.strip().replace("----+", "-----").split("-----")
        tests = zip(tests[::2], tests[1::2])

        result = []

        for input, output in tests:
            input = input.strip()
            output = output.strip()
            result.append({"input": input, "target": output})

        problem_name = file[:-4]
        with open(f"{problem_name}-public.json", "w") as f:
            data = {"testCases": result[:1]}
            f.write(json.dumps(data))

        with open(f"{problem_name}-private.json", "w") as f:
            data = {"testCases": result[1:]}
            f.write(json.dumps(data))


if __name__ == "__main__":
    main()

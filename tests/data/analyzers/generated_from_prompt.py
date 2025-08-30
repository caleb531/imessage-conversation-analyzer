#!/usr/bin/env python3
# generated_from_prompt.py

import pandas as pd

import ica


def main() -> None:
    ica.output_results(
        pd.DataFrame(
            {
                "metric": ["messages", "messages_from_me", "messages_from_them"],
                "total": [1200, 700, 500],
            }
        ).set_index("metric")
    )


if __name__ == "__main__":
    main()

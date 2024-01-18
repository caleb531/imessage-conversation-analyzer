#!/usr/bin/env python3

import pandas as pd


# Export the entire conversation
def analyze(dfs):
    return pd.DataFrame(
        {
            "timestamp": dfs.messages["datetime"],
            # Convert 1/0 to Yes/No
            "is_from_me": (
                dfs.messages["is_from_me"]
                .apply(str)
                .replace("1", "Yes")
                .replace("0", "No")
            ),
            "is_reaction": dfs.messages["is_reaction"],
            # U+FFFC is the object replacement character, which appears as the
            # textual message for every attachment
            "message": dfs.messages["text"].replace(
                r"\ufffc", "(attachment)", regex=True
            ),
        }
    )

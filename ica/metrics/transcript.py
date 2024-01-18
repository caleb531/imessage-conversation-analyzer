#!/usr/bin/env python3

import pandas as pd


def convert_bool_to_yesno(series):
    return series.apply(str).replace("True", "Yes").replace("False", "No")


# Export the entire conversation
def analyze(dfs):
    return pd.DataFrame(
        {
            "timestamp": dfs.messages["datetime"],
            # Convert 1/0 to Yes/No
            "is_from_me": convert_bool_to_yesno(dfs.messages["is_from_me"]),
            "is_reaction": convert_bool_to_yesno(dfs.messages["is_reaction"]),
            # U+FFFC is the object replacement character, which appears as the
            # textual message for every attachment
            "message": dfs.messages["text"].replace(
                r"\ufffc", "(attachment)", regex=True
            ),
        }
    )

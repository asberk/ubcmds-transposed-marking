from argparse import ArgumentParser
import os
import pickle
import bz2
import numpy as np


def to_pklbz2(fname, obj):
    """
    to_pklbz2(fname, obj)

    Write an object `obj` to a pkl.bz2 file. The compression for non-random
    arrays is very good, at the expense of longer write times. Compression is
    *much* better than np.savez_compressed, but not as fast.

    Inputs
    ------
    fname : str
        A filepath (directory included if desired). If the extension is not
        pkl.bz2, then this extension is appended to fname as {fname}.pkl.bz2
    obj : object
        An object of some kind (typically a numpy array)
    """
    shortname = os.path.basename(fname)
    tmp, extension1 = os.path.splitext(shortname)
    extension2 = os.path.splitext(tmp)[-1]
    if (extension1 != ".bz2") and (extension2 != ".pkl"):
        print(f"found extension: {extension2 + extension1}")
        fname = f"{fname}.pkl.bz2"
    pickle.dump(obj, bz2.open(fname, "wb"))
    return


def load_pklbz2(fname):
    """
    load_pklbz2(fname)

    Loads a .pkl.bz2 file whose filepath is fname.

    Inputs
    ------
    fname : str
        A filepath. Does not need to end in .pkl.bz2.
    """
    with bz2.open(fname, "rb") as fp:
        return pickle.load(fp)


def save_files(save_dir, obj_dict):
    raw_dir = save_dir + "raw/"
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)
    for key, byte_string in obj_dict.items():
        to_pklbz2(raw_dir + key + ".pkl.bz2", byte_string)
    print(f"Saved values of obj_dict to {raw_dir}.")
    return


parser = ArgumentParser()

parser.add_argument(
    "--uname", default="aberk", help="GitHub Enterprise username."
)
parser.add_argument(
    "--course", help="DSCI course number (e.g., pass 571 for DSCI 571)",
)
parser.add_argument(
    "--lab",
    help=(
        "The lab number (e.g., pass 4 as the argument if you want to "
        "grade Lab 4)."
    ),
)
parser.add_argument(
    "--exercise",
    nargs="*",
    type=int,
    default=[],
    help=(
        "The exercise number (e.g., pass 3 for Exercise 3; "
        " pass 3 4 5 for Exercises 3--5)"
    ),
)
parser.add_argument(
    "--fname", default=None, help="A regex used to search for a file pattern.",
)
parser.add_argument(
    "--gidpath",
    default="classy.csv",
    type=str,
    help=(
        "The list of the students GitHub IDs to use. "
        "Note: a list with non-matching entries may cause "
        "the script to break or hang."
    ),
)
parser.add_argument(
    "--section",
    default=None,
    type=str,
    help=(
        "Allows filtering by Lab Section (e.g., section L02). Default: all sections."
    ),
)
parser.add_argument(
    "--studentsperpage",
    default=15,
    type=int,
    help=(
        "Each HTML page that's generated will contain "
        "studentsperpage many answers. This is done to manage filesize."
    ),
)
parser.add_argument(
    "--throttle",
    default=0.25,
    type=float,
    help="Min duration to wait (in seconds) between pulling lab files.",
)
parser.add_argument(
    "--doSave",
    default=True,
    type=bool,
    help="Whether to save intermediate lab files as .pkl.bz2 objects.",
)


def format_exercise_num(exercise_num):
    # Parse exercise_num correctly
    if isinstance(exercise_num, (list, tuple)):
        if len(exercise_num) == 0:
            raise ValueError("exercise_num is mandatory")
        elif len(exercise_num) == 1:
            exercise_num = exercise_num[0]
            assert isinstance(exercise_num, np.int), (
                f"Expected integer or list of integers for "
                f"exercise_num but got {exercise_num}."
            )
        else:
            pass
    else:
        assert isinstance(
            exercise_num, np.int
        ), f"expected int or list of ints for exercise_num but got {exercise_num}"
    return exercise_num


def print_info(
    gh_uname,
    course_num,
    lab_num,
    exercise_num,
    fname,
    gid_filepath,
    section,
    throttle,
    spp,
):
    if section is None:
        section_str = "in all sections"
    else:
        section_str = f"in section {section}"

    print(f"Accessing DSCI {course_num} Lab {lab_num} as {gh_uname}.")
    print(f"Looking for GIDs {section_str} matching those in {gid_filepath}.")
    print(f"Searching for exercise {exercise_num} in files matching {fname}.")
    print(f"throttle: {throttle}, students per output page: {spp}")
    return

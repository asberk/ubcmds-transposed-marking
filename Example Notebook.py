# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.3.0
#   kernelspec:
#     display_name: py37
#     language: python
#     name: py37
# ---

# %%
from argparse import ArgumentParser
import numpy as np
import pandas as pd
from github import Github, GithubException
import os
import base64
import re
import time
from IPython.display import display, HTML
import nbformat
from nbconvert import HTMLExporter


# %%
def get_repo(gh, gid, lab_num, course_num="571", year_tag=None, throttle=False):
    """
    get_repo(gh, gid, lab_num, course_num='571', year_tag=None, throttle=False)

    Returns a repo object from the GitHub API

    Inputs
    ------
    gh : github object
    gid : string
        The GitHub ID of the student
    lab_num : str
        The lab number (e.g., lab number '2' of 4)
    course_num : str
        The course number (e.g., DSCI '571')
    year_tag : str
        e.g., 'MDS-2019-20'
    throttle : bool or float
        Whether to slow down this function so that we're not blocked as a bot.
        Default: False

    Returns
    -------
    repo : Github object
    """
    if year_tag is None:
        year_tag = "MDS-2019-20"
    if throttle is True:
        time.sleep(1)
    elif np.isscalar(throttle):
        time.sleep(throttle)
    repo = gh.get_repo(f"{year_tag}/DSCI_{course_num}_lab{lab_num}_{gid}")
    print(f"Fetched: {repo.name}")
    return repo


def get_file_from_repo(fname, repo, throttle=False, use_fuzzy=True):
    """
    get_file_from_repo(fname, repo, throttle=False)

    Returns file with name fname from the repo `repo`.

    Inputs
    ------
    fname : str
        (e.g., lab2.ipynb)
    repo : Github repo object
        (e.g., see get_repo function)
    throttle : bool or float
        Whether to slow down this function so that we're not blocked as a bot.
        Default: False
    use_fuzzy : bool
        If True, fname can be a regex; otherwise we look for exact match.
    """
    if throttle is True:
        time.sleep(1)
    elif np.isscalar(throttle):
        time.sleep(throttle)

    if use_fuzzy:
        dir_contents = repo.get_dir_contents("./")
        contents = next(x for x in dir_contents if re.search(fname, x.path))
    else:
        contents = repo.get_contents(fname)
    print(f"\tfetching: {contents.name}")
    blob = repo.get_git_blob(contents.sha)
    decoded_content = base64.b64decode(bytearray(blob.content, "utf-8"))
    return decoded_content


def fetch_lab_files(
    gh, fname, gid_list, lab_num, course_num, year_tag=None, throttle=False
):
    """
    fetch_lab_files(gh, fname, gid_list, lab_num, course_num, year_tag=None,
                    throttle=False)

    Attempts to return a lab for each student whose gid is in gid_list. Does
    this for lab number lab_num and course number course_num (with year_tag as
    appropriate).

    TODO: Need to check that all names are successfully fetched by
    cross-referencing with gid_list afterward. Either re-try immediately,
    or print out the names that were not fetch.

    Inputs
    ------
    gh : Github object
    fname : str
        (e.g., lab2.ipynb)
    gid_list : array
        A list of each students github id
    lab_num : str
    course_num : str
    year_tag : str or None
    throttle : bool or float
        Whether to slow down this function so that we're not blocked as a bot.
        Default: False
    """
    labs = {}
    if isinstance(gid_list, str) or not np.iterable(gid_list):
        gid_list = [gid_list]
    if not isinstance(lab_num, str):
        lab_num = f"{lab_num}"
    if not isinstance(course_num, str):
        course_num = f"{course_num}"

    for gid in gid_list:
        try:
            labs[gid] = get_file_from_repo(
                fname, get_repo(gh, gid, lab_num, course_num, year_tag)
            )
        except GithubException as ghe:
            print(ghe)
            print("Returning what we have so far...")
            break
    return labs


def persistent_fetch_lab_files(
    gh,
    fname,
    gid_list,
    lab_num,
    course_num,
    year_tag=None,
    num_tries=5,
    throttle=False,
):
    """
    persistent_fetch_lab_files(
        gh,
        fname,
        gid_list,
        lab_num,
        course_num,
        year_tag=None,
        num_tries=5,
        throttle=False,
    )

    A wrapper around fetch_lab_files that tries a few times in case the
    instance gets booted.

    Inputs
    ------
    gh : GitHub instance
    fname : str
    gid_list : array
    lab_num : str
    course_num : str
    year_tag : str or None
    num_tries : int
    throttle : float or None

    Returns
    -------
    lab_files : dict
        keys matching gid_list, with entries that are strings of JSON objects,
        suitable to be passed to nbformat.reads(...)
    """
    lab_files = fetch_lab_files(
        gh, fname, gid_list, lab_num, course_num, year_tag, throttle
    )
    received_keys = np.array(list(lab_files.keys()))
    missing_keys = np.setdiff1d(gid_list, received_keys)
    for i in range(num_tries - 1):
        print(f"Attempt {i + 2}")
        time.sleep(1)
        new_lab_files = fetch_lab_files(
            gh, fname, missing_keys, lab_num, course_num, year_tag, throttle
        )
        for key, value in new_lab_files.items():
            lab_files[key] = value
        received_keys = np.array(list(lab_files.keys()))
        missing_keys = np.setdiff1d(gid_list, received_keys)
        if len(missing_keys) == 0:
            break
    if len(missing_keys) > 0:
        print("-" * 50)
        print("Missing GitHub IDs:")
        print(missing_keys)
        print("-" * 50)
    return lab_files


def get_cell_loc(notebook, exercise_number):
    """
    get_cell_loc(notebook, exercise_number)

    Returns two numbers (a,b), the start and end indices for the cells
    corresponding to the question (i.e., the exercise_number of the lab). For
    example, if exercise_number is 3, then a is the index for the first cell
    for Exercise 3 (the beginning of the problem statement) and b is the index
    for the first cell of Exercise 4.

    Inputs
    ------
    notebook : JSON-like
        (e.g., output of nbformat.reads(lab_file))
    exercise_number : int
        (e.g., 2)
    """
    a = -1
    b = -1
    pattern = r"\#+.*Exercise " + "{ex_num}"
    for i, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "markdown":
            if isinstance(cell["source"], (list, tuple)):
                cell_source = "".join(cell["source"])
            elif isinstance(cell["source"], str):
                cell_source = cell["source"]

            if len(cell_source) == 0:
                pass
            elif re.search(pattern.format(ex_num=exercise_number), cell_source):
                a = i
            elif re.search(
                pattern.format(ex_num=exercise_number + 1), cell_source
            ):
                b = i
        if (a > 0) and (b > 0):
            # No need to search through cells once we've
            # found what we're looking for.
            break
    if a == -1:
        print("Error: get_cell_loc: a not found.")
    elif b == -1:
        print("Error: get_cell_loc: b not found.")
        print("   --> using b = len(notebook['cells'])")
        b = len(notebook["cells"])
    elif a >= b:
        print(f"Error: get_cell_loc: something went wrong: a = {a}, b = {b}")
    return a, b


def get_exercise_from_lab(lab, exercise_num, do_display=False):
    """
    get_exercise_from_lab(lab, exercise_num, do_display=False)

    Takes lab, a string, and uses some nbformat magic to generate html
    containing only the cells corresponding to exercise_num. It displays this
    if do_display is True, and returns the html + css/resources/etc. if
    do_display is False.

    See https://nbconvert.readthedocs.io/en/latest/nbconvert_library.html
    for an extremely helpful tutorial.

    Inputs
    ------
    lab : str
    exercise_num : int
    do_display : bool

    Returns
    -------
    body : HTML string
    resources: dict
    """
    lab_fmt = nbformat.reads(lab, as_version=4)
    a, b = get_cell_loc(lab_fmt, exercise_num)
    lab_fmt["cells"] = lab_fmt["cells"][a:b]

    # Instantiate the exporter with the `basic` template
    html_exporter = HTMLExporter()
    html_exporter.template_file = "basic"

    # Process the notebook we loaded earlier
    (body, resources) = html_exporter.from_notebook_node(lab_fmt)

    if do_display:
        display(HTML(body))
    else:
        return body, resources
    return


def get_exercises_from_lab(lab, exercise_nums, do_display=False):
    """
    get_exercises_from_lab(lab, exercise_nums, do_display=False)

    Takes lab + a list of the exercise numbers to return, and uses some nbformat
    magic to generate html containing only the cells corresponding to
    exercise_num. It displays this if do_display is True, and returns the html +
    css/resources/etc. if do_display is False.

    See https://nbconvert.readthedocs.io/en/latest/nbconvert_library.html
    for an extremely helpful tutorial.

    Inputs
    ------
    lab : str
    exercise_nums : list of int
    do_display : bool

    Returns
    -------
    body : HTML string
    resources: dict
    """
    lab_fmt = nbformat.reads(lab, as_version=4)
    ab_list = [get_cell_loc(lab_fmt, ex_num) for ex_num in exercise_nums]
    cells = sum([lab_fmt["cells"][a:b] for a, b in ab_list], [])
    lab_fmt["cells"] = cells

    # Instantiate the exporter with the `basic` template
    html_exporter = HTMLExporter()
    html_exporter.template_file = "basic"

    # Process the notebook we loaded earlier
    (body, resources) = html_exporter.from_notebook_node(lab_fmt)

    if do_display:
        display(HTML(body))
    else:
        return body, resources
    return


def write_pages_to_files(
    lab_files, gid_pages, exercise_num, lab_num, course_num, save_dir=None
):
    """
    write_pages_to_files(lab_files, gid_pages, exercise_num, lab_num,
                         course_num, save_dir=None)

    Inputs
    ------
    lab_files : list
    gid_pages : dict of lists
    exercise_num : int or list of ints
    lab_num : string
    course_num : string
    save_dir : string

    Output
    ------
    Saves several files to save_dir (default save_dir is './')
    """
    if save_dir is None:
        save_dir = "./"

    if isinstance(exercise_num, (list, tuple)) and (len(exercise_num) != 1):
        exercise_num_str = "".join([f"{x}" for x in exercise_num])
        parser = get_exercises_from_lab
    elif isinstance(exercise_num, np.int):
        exercise_num_str = f"{exercise_num}"
        parser = get_exercise_from_lab
    else:
        print(
            f"Attempting type coercion of exercise_num {exercise_num} "
            f"to int, even though it may be iterable"
        )
        exercise_num = int(exercise_num)
        exercise_num_str = f"{exercise_num}"
        parser = get_exercise_from_lab

    if not isinstance(lab_num, str):
        lab_num = f"{lab_num}"
    if not isinstance(course_num, str):
        course_num = f"{course_num}"

    fname_html = f"DSCI{course_num}_lab{lab_num}_exercise{exercise_num_str}"
    fname_html = fname_html + "_page{page_number}.html"

    # Write paginated HTML pages
    print(f"Writing to {save_dir}:")
    for page_number, gid_page in gid_pages.items():
        fname_page = fname_html.format(page_number=page_number)
        fp = open(save_dir + fname_page, "a")
        fp.write(
            "<head>\n"
            '\t<link rel="stylesheet" href="style0.css">\n'
            '\t<link rel="stylesheet" href="style1.css">'
            "\n</head>\n"
            "\n<body>\n\n"
        )
        for gid in gid_page:
            if gid not in lab_files:
                print(f"gid {gid} not found in lab_files.keys().")
            else:
                fp.write(f"\n\n<h1>{gid}</h1>\n\n")
                fp.write(
                    parser(lab_files[gid], exercise_num, do_display=False)[0]
                )
        fp.write("</body>")
        fp.close()
        print("\t" + f"{fname_page}")
    # Write the CSS files to the same folder
    _, resources = parser(
        list(lab_files.values())[0], exercise_num, do_display=False
    )
    print()
    for i, css_lines in enumerate(resources["inlining"]["css"]):
        with open(save_dir + f"style{i}.css", "w") as fp:
            fp.write(css_lines)
        print("\t" + f"style{i}.css")
    return


def load_ghpw(uname):
    if uname == "aberk":
        with open("ghubcmds.pw", "r") as fp:
            return fp.readline()
    else:
        raise ValueError(f"uname {uname} not recognized.")
    return


# %%
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
    "--fname",
    default=None,
    help="A regex used to search for a file pattern.",
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

# args = parser.parse_args()
args = parser.parse_args(['--course', '572', '--lab', '1', '--exercise', '3', '4', '5', '--section', 'L02', '--throttle', '.1'])
gh_uname = args.uname
course_num = args.course
lab_num = args.lab
exercise_num = args.exercise
fname = args.fname
gid_filepath = args.gidpath
section = args.section
throttle = args.throttle
spp = args.studentsperpage

assert gh_uname is not None, f"Expected gh_uname but found None"
assert course_num is not None, f"Expected course_num but found None"
assert lab_num is not None, f"Expected lab_num but found None"

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

# Default filename
if fname is None:
    fname = f".*lab{lab_num}.*ipynb"

if section is None:
    section_str = "in all sections"
else:
    section_str = f"in section {section}"

print(f"Accessing DSCI {course_num} Lab {lab_num} as {gh_uname}.")
print(f"Looking for GIDs {section_str} matching those in {gid_filepath}.")
print(f"Searching for exercise {exercise_num} in files matching {fname}.")
print(f"throttle: {throttle}, students per output page: {spp}")

# %%
# Classy CSV should be the CSV file containing all of the github ids
gid_df = pd.read_csv(gid_filepath)  # pd.read_csv("./classy.csv")
if section is not None:
    gid_df = gid_df.loc[
        gid_df.filter(regex="[Ss]ection").values.ravel() == section
    ]
gid_list = gid_df.id0.values

num_pages = gid_list.size // spp + 1
gid_pages = {
    page: gid_list[spp * page : (spp * page + spp)]
    for page in range(num_pages)
}

# initialize github instance
password = load_ghpw(gh_uname)
gh = Github(
    login_or_token=gh_uname,
    password=password,
    base_url="https://github.ubc.ca/api/v3",
)

# download lab files
lab_files = persistent_fetch_lab_files(
    gh, fname, gid_list, lab_num, course_num, throttle=throttle
)

# set and create directory
save_dir = f"./DSCI{course_num}/Lab{lab_num}/"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# %%
import util

# %%
doSave = True
# Useful in case something goes wrong.
if doSave is True:
    raw_dir = save_dir + "raw/"
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)
    for key, byte_string in lab_files.items():
        util.to_pklbz2(raw_dir + key + ".pkl.bz2", byte_string)


# %%
# !open {save_dir}

# %%
exercise_num = [3, 4]

# %%
# write exercises to HTML pages
write_pages_to_files(
    lab_files,
    gid_pages,
    exercise_num,
    lab_num,
    course_num,
    save_dir=save_dir,
)

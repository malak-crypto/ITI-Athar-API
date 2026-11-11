# Tech News API

A small Python program that fetches English technology headlines from the free
[GNews API](https://gnews.io/) and displays them in a scrollable desktop
window. Each story shows its title, source, publication time, description,
and a button to open the article.

The free plan requires a GNews API key, allows up to 100 requests per day and
10 articles per request, and delays headlines. Get a free key at
https://gnews.io/register.

## Get the project

Either download the repository as a ZIP from GitHub using **Code → Download
ZIP** and extract it, or clone it if Git is installed:

```text
git clone https://github.com/malak-crypto/TechNewsAPI.git
cd TechNewsAPI
```

In Anaconda Prompt, change to the extracted or cloned project folder before
running the setup commands.

## Set up the Anaconda environment

Create the environment once:

```text
conda create --name tech-news-api python=3.13 pip
```

Then activate it and install the project dependencies:

```text
conda activate tech-news-api
python -m pip install -r requirements.txt
```

If you already created the environment, skip the `conda create` command.
Afterward, activate the environment whenever you open a new Anaconda Prompt.

`requirements.txt` lists the two third-party packages the program needs:
`requests` for the API call and `python-dotenv` for reading `.env`. Tkinter,
used for the desktop window, and the other standard-library modules come with
Python; they don't need to be installed separately with pip.

## Configure your API key

Copy the example file to `.env`:

```text
copy .env.example .env
```

Open `.env` and replace the example value with your GNews API key:

```text
GNEWS_API_KEY=your_actual_api_key
```

Keep `.env` private; it is excluded from Git uploads by `.gitignore`.

## Run

Start the desktop news window:

```text
python main.py
```

The window fetches headlines at startup. Click **Refresh** or press **F5** to
fetch them again. To print a text summary in the terminal instead, run:

```text
python main.py --cli
```

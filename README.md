**forked from [Alan Robertson](https://github.com/Alan-Robertson/usyd_timesheet_automation)**

## Because Online Timesheet Submissions are a Pain

My employer requires that we manually track and transcribe data from our own records of time worked into their online system. We are not paid for the time spent doing this, but without doing it we're not paid at all.

The system itself has several bugs/flaws/surprise features which makes this a painful event.

As a result this selenium script exists. It's very hard coded and very bare bones but it gets the job done.

## Usage ##

```bash
python timesheet_submitter.py <csv file> [csv files ...]
```

After running the script you'll be presented with the login page; do this yourself (so I don't have to touch your credentials) and press enter on the script once you've finished with this.

After that the script should fill everything out until you need to enter your timesheet submitter and lodge. The script will not press the lodge button for you just to be sure.

NOTE: Make sure you do not include any `+`, `,` or `/` characters in your script.


## CSV Format ##

The csv you provide should contain the following columns:

```
DATE, Unit of study, Paycode, Units, Start Time, [Required on site], [responsibility code], [project code], [Analysis Code], [Topic], [Topic details]
```

Date should be in the format `dd/mm/yyyy` and start time should be in the format `hh:mm`.

"Required on site" should be `Y` or `N` or empty.

see `csvs/sample.csv`

# next_timesheet.py
The schedule for each week is more or less the same.
Since timesheets are submitted every 2 weeks, this script will take in a timesheet,
add 14 days to each date and output a new timesheet.

**Example:**

```bash
python next_timesheet.py csvs/sample.csv  csvs/week_4.csv
```
**forked from [Alan Robertson](https://github.com/Alan-Robertson/usyd_timesheet_automation)**

## Because Online Timesheet Submissions are a Pain

My employer requires that we manually track and transcribe data from our own records of time worked into their online system. We are not paid for the time spent doing this, but without doing it we're not paid at all.

The system itself has several bugs/flaws/surprise features which makes this a painful event.

As a result this selenium script exists. It's very hard coded and very bare bones but it gets the job done.

## WARNING: Security risk ##

Please **DO NOT** put your credentials into the script. **DO NOT PUT THEM IN PLAIN TEXT**.
You can use `input()` to make a prompt. But hardcording your credentials would make your account **VULNERABLE**.

**IF YOU DO NOT KNOW HOW TO USE IT WITH PASSWORD MANAGER, OR A HARDWARE PASSKEY. DO NOT USE AUTOMATED LOGIN FEATURE**

## Usage ##

```bash
python timesheet_submitter.py -m {auto, csv} -f csvfile [csvfile ...]
```

You will need your TOTP secret key and a password manager to automate your login process.

In your password manager, create a service name: *USYD-CREDENTIAL* and add these three fields.
```
UNIKEY: <Your unikey>
PASSWORD: <Your password>
TOTP_SECRET: <Your TOTP secret key>
```

If you don't have your TOTP secret, when 2FA is needed, you will be prompted to complete it manually. To do that, clear the field TOTP_SECRET, or do not set it in the first place.

After that the script should fill everything out until you need to enter your timesheet submitter and lodge. The script will not press the lodge button for you just to be sure.

NOTE: Make sure you do not include any `+`, `,` or `/` characters in your script.

## Modes ##

### Auto Mode ###
In auto mode, you will need to provide csv files as templates. The script will automatically add 7 days to your original date.Before filling the form, the csv file would be updated.

### CSV Mode ###
In CSV Mode, the script will only fill the form as what is in CSV file, and you can pass multiple CSV files as arguments.

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

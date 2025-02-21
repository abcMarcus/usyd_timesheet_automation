import sys
import csv
from datetime import datetime, timedelta

def add_days_to_csv(infile, outfile):
    with open(infile, mode='r', newline='', encoding='utf-8') as fin, \
            open(outfile, mode='w', newline='', encoding='utf-8') as fout:

        reader = csv.reader(fin)
        writer = csv.writer(fout)

        for row in reader:
            if row:
                original_date = datetime.strptime(row[0], "%d/%m/%Y")
                new_date = original_date + timedelta(days=14)
                row[0] = new_date.strftime("%d/%m/%Y")
                writer.writerow(row)
            else:
                writer.writerow([])

    print(f"Processed file saved to {outfile}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <infile> <outfile>")
    else:
        add_days_to_csv(sys.argv[1], sys.argv[2])
